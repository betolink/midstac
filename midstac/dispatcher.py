"""
Query dispatcher for earthaccess and pystac_client
"""

import logging
import traceback
from typing import Any, Optional
from urllib.parse import urlparse

import earthaccess
from pystac_client import Client

from .models import DatasetSummary, Link

logger = logging.getLogger(__name__)


class DatasetFormattingError(Exception):
    """Raised when dataset formatting fails"""

    pass


class AuthenticationError(Exception):
    """Raised when authentication fails"""

    pass


class SearchError(Exception):
    """Raised when search operations fail"""

    pass


def is_valid_url(url: str) -> bool:
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def format_nasa_dataset(result) -> DatasetSummary:
    try:
        links = []
        for link in result.get_umm("RelatedUrls") or []:
            if "URL" in link and "Type" in link:
                links.append(Link(url=link["URL"], rel=link["Type"]))

        summary_text = result.abstract()
        if "DOI" in result.get_umm("DOI"):
            doi = str(result.get_umm("DOI")["DOI"])
        else:
            doi = "Unavailable"

        return DatasetSummary(
            source="NASA CMR",
            id=result.concept_id(),
            doi=doi,
            title=result.get_umm("EntryTitle") or "",
            summary=summary_text[:500],
            links=links,
        )

    except Exception as e:
        logger.error(f"Failed to format NASA dataset {result}: {e}\n{traceback.format_exc()}")
        raise DatasetFormattingError(f"Could not format NASA dataset: {e}") from e


def format_stac_dataset(result) -> DatasetSummary:
    """Format a single dataset record to return to the tool

    Args:
        dataset: A DatasetSummary object from earthaccess
    """
    return DatasetSummary(
        source="STAC",
        id=result.id,
        title=result.title,
        summary=result.description[0:500],
        links=[Link(url=link.target, rel=link.rel) for link in result.links if is_valid_url(link.target)],
    )


class QueryDispatcher:
    """Dispatch queries to earthaccess and pystac_client based on parameters"""

    # Common STAC catalog URLs
    STAC_CATALOGS = {
        "nasa": "https://cmr.earthdata.nasa.gov/stac",
        "earth_search": "https://earth-search.aws.element84.com/v1",
        "planetary_computer": "https://planetarycomputer.microsoft.com/api/stac/v1",
        "maap": "https://stac.maap-project.org/",
    }

    def __init__(self):
        """Initialize the dispatcher"""
        self.authenticate_earthaccess()

    def authenticate_earthaccess(self) -> bool:
        """
        Authenticate with NASA Earthdata

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.auth = earthaccess.login()
            logger.info("Earthaccess authentication successful")
            return self.auth.authenticated
        except Exception as e:
            logger.error(f"Earthaccess authentication error: {e}")
            return False

    def search_earthaccess_collections(
        self,
        keyword: Optional[str] = None,
        bbox: Optional[list[float]] = None,
        temporal: Optional[tuple] = None,
        count: Optional[int] = 10,
        **kwargs,
    ) -> list[DatasetSummary]:
        """
        Search for granules using earthaccess

        Args:
            keyword: a string with search keywords e.g. "water quality" or "vegetation index"
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
            temporal: Temporal range as (start_date, end_date)
            **kwargs: Additional search parameters

        Returns:
            List of collection results
        """
        try:
            # Try to authenticate if not already done
            if not self.auth.authenticated:
                self.authenticate_earthaccess()

            search_params = {}

            if keyword:
                search_params["keyword"] = keyword
            else:
                search_params["keyword"] = "*"

            if bbox:
                search_params["bounding_box"] = tuple(bbox)

            if temporal:
                search_params["temporal"] = temporal

            # Merge additional kwargs
            search_params.update(kwargs)
            search_params["count"] = count

            logger.info(f"Earthaccess search parameters: {search_params}")

            results = earthaccess.search_datasets(**search_params)
            collections = []
            for result in results:
                logger.info(f"Found Earthaccess dataset: {result.concept_id()}")
                collections.append(format_nasa_dataset(result))

            return collections
        except Exception as e:
            print(f"Earthaccess search error: {e}")
            return []

    def search_stac_collections(
        self,
        catalog_url: Optional[str] = STAC_CATALOGS["maap"],
        keywords: Optional[list[str]] = None,
        bbox: Optional[list[float]] = None,
        datetime: Optional[str] = None,
        limit: int = 10,
        **kwargs,
    ) -> list[DatasetSummary]:
        """
        Search STAC catalog using pystac_client

        Args:
            catalog_url: STAC catalog URL (default: NASA CMR STAC)
            keywords: Keywords to search for in collections
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)
            datetime: ISO 8601 datetime string or range (e.g., '2020-01-01/2020-12-31')
            limit: Maximum number of items to return
            **kwargs: Additional search parameters

        Returns:
            List of STAC collections
        """
        try:
            if not catalog_url:
                catalog_url = self.STAC_CATALOGS["maap"]

            catalog = Client.open(catalog_url)

            # Build search parameters
            search_params = {}

            if keywords:
                keyword_query = " or ".join(keywords.split()) if isinstance(keywords, str) else " or ".join(keywords)
                search_params["q"] = keyword_query

            if bbox:
                search_params["bbox"] = bbox

            if datetime:
                search_params["datetime"] = datetime

            search_params.update(kwargs)
            logger.info(f"STAC search parameters: {search_params}")

            search = catalog.collection_search(**search_params)

            collections = []
            result_count = search.matched()
            logger.info(f"STAC search found {result_count} collections")
            for result in search.collection_list():
                logger.info(f"Found STAC collection: {result.id}")
                collections.append(format_stac_dataset(result))

            return collections
        except Exception as e:
            logger.info(f"STAC search error: {e}")
            return []

    def dispatch_collection_query(
        self,
        params: dict[str, Any],
        bbox: Optional[list[float]],
        keywords: list[str],
        max_results: int = 10,
        source: str = "all",
    ) -> list:
        """
        Dispatch query to appropriate service based on parameters

        Args:
            params: Dictionary of extracted parameters from natural language

        Returns:
            Dictionary with results from earthaccess and/or STAC
        """

        bbox = params.get("bbox")
        geolocated_corrected_bbox = bbox
        if geolocated_corrected_bbox != bbox:
            logger.info(
                f"The extracted bbox does not agree with the geolocated bbox. Using LLM {geolocated_corrected_bbox} instead of {bbox}"
            )
            bbox = geolocated_corrected_bbox

        temporal = params.get("temporal", {})

        if not keywords:
            keywords = params.get("query", "").split()

        temporal_tuple = None
        datetime_str = None

        if temporal:
            start = temporal.get("start_date")
            end = temporal.get("end_date", start)
            if start:
                temporal_tuple = (start, end)
                datetime_str = f"{start}/{end}" if end else start

        results_earthaccess = []
        results_stac = []

        if source in ("nasa", "all"):
            try:
                for keyword in keywords:
                    results_earthaccess.extend(
                        self.search_earthaccess_collections(
                            keyword=keyword, bbox=bbox, temporal=temporal_tuple, count=max_results
                        )
                    )
            except Exception as e:
                logger.error(f"Error searching earthaccess: {e}")

        if source in (
            "maap",
            "all",
            "stac",
            "esa",
        ):
            try:
                for keyword in keywords:
                    results_stac.extend(
                        self.search_stac_collections(
                            keywords=[keyword], bbox=bbox, datetime=datetime_str, limit=max_results
                        )
                    )
            except Exception as e:
                logger.error(f"Error searching STAC: {e}")

        return results_earthaccess + results_stac

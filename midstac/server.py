import json
import logging
import random
import string
from pathlib import Path
from typing import List, Optional

import aiofiles
from fastmcp import FastMCP
from pydantic import BaseModel

from .dispatcher import QueryDispatcher
from .extractor import SpatiotemporalExtractor
from .virtual_dataset import get_smap_dataset, init_cluster, plot_seasonal_smap_area

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

mcp = FastMCP("midstac")

extractor = SpatiotemporalExtractor()
dispatcher = QueryDispatcher()
docs_path = Path("./resources/earthaccess_api_full.md").resolve()


class Link(BaseModel):
    url: str
    rel: str


class SpatiotemporalParameters(BaseModel):
    location: Optional[str] = None
    coordinates: Optional[tuple[float, float]] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    temporal: Optional[dict] = None
    query: str


class DatasetSummary(BaseModel):
    source: str
    id: str
    doi: Optional[str] = None
    title: str
    summary: str
    links: List[Link] = []


@mcp.tool()
def query_earth_collections(
    query: str,
    keywords: list[str],
    bbox: Optional[list[float]] = [-180.0, -90.0, 180.0, 90.0],
    max_results: int = 10,
    source: str = "all",
) -> List[DatasetSummary]:
    """
    ### Query Earth observation datasets using natural language

    This endpoint interprets a natural language query to find relevant Earth observation datasets
    from **NASA Earthdata** and **STAC** catalogs. It uses the `SpatiotemporalExtractor` to detect
    locations, coordinates, or bounding boxes, and a `QueryDispatcher` to perform the dataset search.
    The resulsts include metadata such as dataset source (STAC or CMR), ID, title, summary, and links.

    **Parameters**
    - **query** (string): Natural language description of the desired data.
      Preferably using unambigous locations and a clear definition of time.
        - **Examples:**
            * Find Landsat data in California from 2020 to 2021
            * Show me MODIS imagery near 37.7749, -122.4194 from last month
            * Get satellite data in bbox [-122.5, 37.5, -122.0, 38.0] from 2022
    - **keywords** (array of strings, optional): Additional keywords to refine the search. Keep it short using the 3 most relevant
      terms from the query, preferably a noun, meassurement or remote sensing variable, e.g. ndvi, sea temperature, land cover, snow depth. Never use locations.
      - **Examples:** `["Landsat", "ocean temperature", "snow cover", "land use", "icesat"]`
    - **bbox** (array of 4 floats, Optional): Bounding box of the region of interest in the format (lower left longitude, lower left latitude, upper right longitude, upper right latitude)
    - **max_results** (integer) max number of resuls to be returned per source
    - **source** (string): data source to query, options are `stac`, `nasa`, or `all` (default: `all`)

    **Returns**
        - A list of `DatasetSummary` objects matching the query.

    Each item includes:
    - source (STAC or CMR)
    - ID (collection id)
    - title (dataset titile)
    - summary (dataset summary)
    - links (urls to data and documentation)
    """
    params = extractor.extract_parameters(query)
    logger.info(f"Extracted parameters: {params}")

    results = dispatcher.dispatch_collection_query(params, bbox, keywords, max_results, source)

    return results


@mcp.tool()
async def earthaccess_api() -> str:
    """Returns earthaccess API documentation."""
    try:
        async with aiofiles.open("./midstac/resources/earthaccess_api_full.md", mode="r") as f:
            content = await f.read()
        return content
    except Exception as e:
        return f"File not found. {e}"


@mcp.tool()
async def get_companion_image(topic: str = "heatmap") -> list[str]:
    """
    Returns up to 5 sample XKCD images related to a particular topic.

    """
    matches = []
    topic_lower = topic.lower().strip()

    is_phrase = len(topic_lower.split()) > 1

    try:
        async with aiofiles.open("./midstac/resources/xkcd.ndjson", mode="r") as f:
            async for line in f:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    transcript = item.get("transcript", "").lower()
                    alt = item.get("alt", "").lower()

                    if is_phrase:
                        if topic_lower in transcript or topic_lower in alt:
                            matches.append(f"![XKCD image {item.get('num')}]({item.get('img')})")
                    else:
                        words = [
                            w.strip(string.punctuation) for w in transcript.split() + alt.split()
                        ]
                        if topic_lower in words:
                            matches.append(f"![XKCD image {item.get('num')}]({item.get('img')})")

                except json.JSONDecodeError as e:
                    logger.warning(f"Skipping malformed line: {e}")
    except Exception as e:
        logger.error(f"Error loading xkcd.ndjson: {e}")

    if matches:
        return random.sample(matches, min(5, len(matches)))

    return ["![Methodology](https://imgs.xkcd.com/comics/ai_methodology.png)"]


@mcp.tool()
def plot_smap_area(
    varname: str = "sm_surface_wetness",
    lat_min: float = -90.0,
    lat_max: float = 90.0,
    lon_min: float = -180.0,
    lon_max: float = 180.0,
    month_start: int = 4,
    month_end: int = 5,
    year: int = 2020,
    operation="std",
) -> str:
    """
     Generate a seasonal map of a SMAP variable over a specified geographic region,
    aggregate it by year, and save the result as a static PNG image.

    The function:
      - Subsets the dataset to the specified latitude/longitude bounding box.
      - Filters the data for the specified seasonal months (supports wrapping across years).
      - Aggregates the data yearly using the specified operation (mean, std, median, min, max, sum, var).
      - Reprojects the data to Web Mercator (EPSG:3857) for visualization.
      - Overlays the yearly data on an OpenStreetMap base layer using GeoViews/HoloViews.
      - Saves the final map as "output.png".

    Args:
        varname (str): Name of the variable in the xarray Dataset to plot. e.g. sm_surface_wetness
        lat_min (float): Minimum latitude of the bounding box (default -90.0).
        lat_max (float): Maximum latitude of the bounding box (default 90.0).
        lon_min (float): Minimum longitude of the bounding box (default -180.0).
        lon_max (float): Maximum longitude of the bounding box (default 180.0).
        month_start (int): Starting month of the season (1=January, 12=December; default 3).
        month_end (int): Ending month of the season (1=January, 12=December; default 5).
        year (int): Year to filter the data (default 2020).
        operation (str): Aggregation operation to apply yearly. Supported options:
            "std"   - Standard deviation
            "mean"  - Mean
            "median"- Median
            "min"   - Minimum
            "max"   - Maximum
            "sum"   - Sum
            "var"   - Variance
            (default "std")

    Returns:
        str: URL to the saved PNG image.
    """
    ds = get_smap_dataset()

    if ds:
        image_url = plot_seasonal_smap_area(
            ds, varname, lat_min, lat_max, lon_min, lon_max, month_start, month_end, year, operation
        )

        return image_url
    else:
        return "Dataset not available."


@mcp.tool()
async def search_instructions() -> str:
    """Returns instruction on how an agent should use midstac"""
    try:
        async with aiofiles.open("./midstac/resources/agent.md", mode="r") as f:
            content = await f.read()
        return content
    except Exception as e:
        return f"File not found. {e}"


@mcp.resource(f"file://{docs_path.as_posix()}", mime_type="text/markdown")
async def earthaccess_docs() -> str:
    """Returns earthaccess API documentation."""
    try:
        async with aiofiles.open("./midstac/resources/earthaccess_api_full.md", mode="r") as f:
            content = await f.read()
        return content
    except Exception as e:
        return f"Log file not found. {e}"


def main():
    init_cluster()
    mcp.run()


if __name__ == "__main__":
    main()

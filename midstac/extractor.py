import logging
import os
import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import requests
from dateutil import parser as date_parser
from pydantic import BaseModel

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class SpatiotemporalParameters(BaseModel):
    location: Optional[str] = None
    coordinates: Optional[tuple[float, float]] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    temporal: Optional[dict] = None
    query: str


class SpatiotemporalExtractor:
    """Extract spatiotemporal parameters from natural language queries"""

    LOCATION_PATTERNS = [
        r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"over\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"at\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        r"near\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
    ]

    COORDINATE_PATTERNS = [
        r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)",
        r"lat[itude]*[:=\s]+(-?\d+(?:\.\d+)?)[,\s]+lon[gitude]*[:=\s]+(-?\d+(?:\.\d+)?)",
        r"(-?\d+(?:\.\d+)?)\s*[NS]\s*,?\s*(-?\d+(?:\.\d+)?)\s*[EW]",
    ]

    BBOX_PATTERNS = [
        r"bbox\s*(?:[:=]\s*)?\[?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]?",
        r"bounds?\s*(?:[:=]\s*)?\[?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\]?",
    ]

    TEMPORAL_KEYWORDS = {
        "today": 0,
        "yesterday": -1,
        "last week": -7,
        "last month": -30,
        "last year": -365,
    }

    DATE_RANGE_PATTERNS = [
        r"from\s+([\w\s,\-:]+?)\s+to\s+([\w\s,\-:]+)",
        r"between\s+([\w\s,\-:]+?)\s+and\s+([\w\s,\-:]+)",
        r"since\s+([\w\s,\-:]+)",
        r"after\s+([\w\s,\-:]+)",
        r"before\s+([\w\s,\-:]+)",
        r"in\s+(\d{4})",
        r"during\s+([\w\s,\-:]+)",
    ]

    def __init__(self):
        """Initialize the extractor"""
        self.geocoding_api_key = os.getenv("GEOCODING_API_KEY", None)
        self.geocoding_location_url = "https://api.geoapify.com/v1/geocode/search"
        self.geocoding_place_details = "https://api.geoapify.com/v2/place-details"

    def extract_location(self, query: str) -> Optional[str]:
        """
        Extract location name from natural language query

        Args:
            query: Natural language query string

        Returns:
            Location name if found, None otherwise
        """
        for pattern in self.LOCATION_PATTERNS:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        return None

    def extract_geolocation_bbox(self, location: str) -> Optional[list[float]]:
        """
        Placeholder for geocoding location names to coordinates.
        In a real implementation, this would call a geocoding API.

        Args:
            location: Location name string
        Returns:
            List of [latitude, longitude] if found, None otherwise
        """

        url = f"{self.geocoding_location_url}?text={location}&apiKey={self.geocoding_api_key}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        first_feature = data.get("features", [])[0]
        if first_feature:
            bbox = first_feature.get("bbox")
            return bbox
        else:
            return None

    def extract_coordinates(self, query: str) -> Optional[Tuple[float, float]]:
        """
        Extract coordinates (lat, lon) from query

        Args:
            query: Natural language query string

        Returns:
            Tuple of (latitude, longitude) if found, None otherwise
        """
        for pattern in self.COORDINATE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    # Validate coordinate ranges
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        return (lat, lon)
                except (ValueError, IndexError):
                    continue
        return None

    def extract_bbox(self, query: str) -> Optional[list[float]]:
        """
        Extract bounding box from query

        Args:
            query: Natural language query string

        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat) if found, None otherwise
        """
        for pattern in self.BBOX_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    coords = [float(match.group(i)) for i in range(1, 5)]
                    return coords
                except (ValueError, IndexError):
                    continue
        return None

    def extract_temporal(self, query: str) -> Optional[Dict[str, str]]:
        """
        Extract temporal parameters from query

        Args:
            query: Natural language query string

        Returns:
            Dictionary with 'start_date' and/or 'end_date' if found, None otherwise
        """
        query_lower = query.lower()

        # Check for temporal keywords
        for keyword, days_offset in self.TEMPORAL_KEYWORDS.items():
            if keyword in query_lower:
                date = datetime.now() + timedelta(days=days_offset)
                return {
                    "start_date": date.strftime("%Y-%m-%d"),
                    "end_date": datetime.now().strftime("%Y-%m-%d"),
                }

        # Check for date range patterns
        for pattern in self.DATE_RANGE_PATTERNS:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                try:
                    if "from" in pattern or "between" in pattern:
                        start_str = match.group(1).strip()
                        end_str = match.group(2).strip()

                        # Check if both are just years (4 digits)
                        if re.match(r"^\d{4}$", start_str) and re.match(r"^\d{4}$", end_str):
                            return {
                                "start_date": f"{start_str}-01-01",
                                "end_date": f"{end_str}-12-31",
                            }

                        start_date = date_parser.parse(start_str, fuzzy=True)
                        end_date = date_parser.parse(end_str, fuzzy=True)
                        return {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": end_date.strftime("%Y-%m-%d"),
                        }
                    elif "since" in pattern or "after" in pattern:
                        start_date = date_parser.parse(match.group(1), fuzzy=True)
                        return {
                            "start_date": start_date.strftime("%Y-%m-%d"),
                            "end_date": datetime.now().strftime("%Y-%m-%d"),
                        }
                    elif "before" in pattern:
                        end_date = date_parser.parse(match.group(1), fuzzy=True)
                        return {
                            "end_date": end_date.strftime("%Y-%m-%d"),
                        }
                    elif "in" in pattern and len(match.group(1)) == 4:
                        year = match.group(1)
                        return {
                            "start_date": f"{year}-01-01",
                            "end_date": f"{year}-12-31",
                        }
                    elif "during" in pattern:
                        date = date_parser.parse(match.group(1), fuzzy=True)
                        return {
                            "start_date": date.strftime("%Y-%m-%d"),
                            "end_date": date.strftime("%Y-%m-%d"),
                        }
                except (ValueError, AttributeError):
                    continue

        return None

    def extract_parameters(self, query: str) -> SpatiotemporalParameters:
        """
        Extract all spatiotemporal parameters from a natural language query

        Args:
            query: Natural language query string

        Returns:
            Dictionary containing extracted parameters:
            - location: str (location name)
            - coordinates: tuple (lat, lon)
            - bbox: tuple (min_lon, min_lat, max_lon, max_lat)
            - temporal: dict (start_date, end_date)
            - query: str (original query)
        """
        params = {
            "query": query,
        }

        # Extract location
        location = self.extract_location(query)
        if location:
            params["location"] = location

        # Extract coordinates
        coords = self.extract_coordinates(query)
        if coords:
            params["coordinates"] = coords

        # Extract bounding box
        bbox = self.extract_bbox(query)
        if bbox:
            params["bbox"] = bbox

        # Extract temporal parameters
        temporal = self.extract_temporal(query)
        if temporal:
            params["temporal"] = temporal

        if location and (not bbox and not coords):
            params["bbox"] = self.extract_geolocation_bbox(location)
            logger.info(f"Geocoding location: {location}, results in bbox: {params['bbox']}")

        return params

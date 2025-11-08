"""
Centralized Pydantic models for midstac
"""

from typing import Optional

from pydantic import BaseModel


class Link(BaseModel):
    """Represents a link in STAC/NASA datasets"""

    url: str
    rel: str


class SpatiotemporalParameters(BaseModel):
    """Represents extracted spatiotemporal parameters from natural language queries"""

    location: Optional[str] = None
    coordinates: Optional[tuple[float, float]] = None
    bbox: Optional[tuple[float, float, float, float]] = None
    temporal: Optional[dict] = None
    query: str


class DatasetSummary(BaseModel):
    """Represents a summary of a dataset from various sources"""

    source: str
    id: str
    doi: Optional[str] = None
    title: str
    summary: str
    links: list[Link] = []

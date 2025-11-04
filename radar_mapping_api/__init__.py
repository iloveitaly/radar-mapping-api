"""
radar-mapping-api: A Python client for the Radar.io geocoding and mapping API.

This package provides a type-safe, production-ready client for interacting with
Radar.io's geocoding, reverse geocoding, place search, and address validation APIs.
"""

from radar_mapping_api.client import RadarClient
from radar_mapping_api.helpers import geocode_coordinates, geocode_postal_code
from radar_mapping_api.models import (
    Address,
    Chain,
    GeocodeResponse,
    GeocodeResult,
    Geometry,
    Meta,
    Place,
    SearchPlacesResponse,
    TimeZone,
    ValidateAddressResponse,
)

__all__ = [
    "RadarClient",
    "geocode_coordinates",
    "geocode_postal_code",
    "Address",
    "Chain",
    "GeocodeResponse",
    "GeocodeResult",
    "Geometry",
    "Meta",
    "Place",
    "SearchPlacesResponse",
    "TimeZone",
    "ValidateAddressResponse",
]

__version__ = "0.1.0"

"""Pydantic models for Radar.io API responses."""

from typing import Any

from pydantic import BaseModel


class Geometry(BaseModel):
    """
    GeoJSON-compliant geometry object.

    Used to represent coordinates for addresses and places in the Radar API.
    """

    type: str
    coordinates: list[float]


class TimeZone(BaseModel):
    """
    Time zone information for a specific geographical location.

    Includes UTC/DST offsets and current local time.
    """

    id: str | None = None
    name: str
    code: str
    currentTime: str
    utcOffset: int
    dstOffset: int


class Address(BaseModel):
    """
    Detailed representation of a physical address.

    Contains granular fields like street, city, and state, along with geographical
    coordinates and time zone metadata.
    """

    latitude: float
    longitude: float
    geometry: Geometry
    country: str
    countryCode: str
    countryFlag: str
    county: str | None = None
    city: str | None = None
    state: str | None = None
    stateCode: str | None = None
    postalCode: str | None = None
    layer: str
    formattedAddress: str
    addressLabel: str
    timeZone: TimeZone | None = None
    distance: float | None = None
    confidence: str | None = None
    borough: str | None = None
    neighborhood: str | None = None
    number: str | None = None
    street: str | None = None


class Meta(BaseModel):
    """
    API response metadata.

    Primarily used to communicate the HTTP status code of the Radar request.
    """

    code: int


class GeocodeResponse(BaseModel):
    """
    Radar API response for geocoding requests.

    Returns a list of potential address matches for a given query or coordinate.
    """

    meta: Meta
    addresses: list[Address]


class Chain(BaseModel):
    """
    Business chain data for a place.

    Identifies the parent organization and provides metadata for brands.
    """

    name: str
    slug: str
    externalId: str | None = None
    metadata: dict[str, Any] | None = None


class Place(BaseModel):
    """
    A Point of Interest (POI) or specific business location.

    Includes category information and the business chain if applicable.
    """

    name: str
    chain: Chain | None = None
    categories: list[str]
    location: Geometry


class SearchPlacesResponse(BaseModel):
    """
    Radar API response for place search requests.

    Returns a list of places matching the search criteria.
    """

    meta: Meta
    places: list[Place]


class ValidateAddressResponse(BaseModel):
    """
    Response for Radar's address validation endpoint.

    The response includes the validated `address` object and an opaque `result`
    payload with provider-specific fields.
    """

    meta: Meta
    address: Address | None = None
    result: dict[str, Any] | None = None


class GeocodeResult(BaseModel):
    """
    Result of geocoding a location with extracted coordinates and address info.

    Meant to be a simple version of what comes back from Radar so we can easily swap out
    radar with any other system.
    """

    lat: float
    lon: float
    address1: str | None = None
    address2: str | None = None
    postal_code: str | None
    city: str | None
    state_code: str | None
    country_code: str | None = None
    formatted_address: str | None

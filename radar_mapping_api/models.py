"""Pydantic models for Radar.io API responses."""

from typing import Any

from pydantic import BaseModel


class Geometry(BaseModel):
    type: str
    coordinates: list[float]


class TimeZone(BaseModel):
    id: str | None = None
    name: str
    code: str
    currentTime: str
    utcOffset: int
    dstOffset: int


class Address(BaseModel):
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
    code: int


class GeocodeResponse(BaseModel):
    meta: Meta
    addresses: list[Address]


class Chain(BaseModel):
    name: str
    slug: str
    externalId: str | None = None
    metadata: dict[str, Any] | None = None


class Place(BaseModel):
    name: str
    chain: Chain | None = None
    categories: list[str]
    location: Geometry


class SearchPlacesResponse(BaseModel):
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
    postal_code: str | None
    city: str | None
    state_code: str | None
    formatted_address: str | None

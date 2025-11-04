"""

- api docs are here: https://docs.radar.com/api
- there's no py library that's not very old + unmaintained, so we've built this directly

Possible future alternatives:

- https://github.com/fitnr/censusgeocode

TODO

- compact should be used instead of dict construction
- look into more funcy uses here
- if `20:17:01 py_dev.1  | 2025-08-24T20:17:01.094386Z [info     ] Retrying app.lib.radar.RadarClient._make_request in 2.0 seconds as it raised HTTPStatusError: Client error '402 Payment Required' for url 'https://api.radar.io/v1/search/autocomplete?query=801&countryCode=US'` we should not retry and error immediately
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

import httpx
import sentry_sdk
from pydantic import BaseModel
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

if TYPE_CHECKING:
    pass

# Global radar client instance
_radar_client: Optional["RadarClient"] = None


def _is_retryable_httpx_error(exception: BaseException) -> bool:
    """
    return True to retry, False to stop retrying.

    avoid retrying on HTTP 402 payment required, which means quota exceeded.
    """
    if not isinstance(exception, httpx.HTTPError):
        return False

    if isinstance(exception, httpx.HTTPStatusError):
        if exception.response is not None and exception.response.status_code == 402:
            return False

    return True


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


class RadarClient:
    """
    A client class for interacting with the Radar.io Geocoding API using httpx.
    This class handles authentication via API key and provides methods for forward geocoding
    with exponential backoff on errors using the tenacity library.
    """

    def __init__(self, api_key: str):
        """
        Initializes the RadarClient with the provided API key.

        :param api_key: The publishable API key for authentication.
        """
        if not api_key:
            raise ValueError("API key must be provided.")

        self.api_key: str = api_key
        self.base_url: str = "https://api.radar.io/v1/"

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=0, max=32),
        retry=retry_if_exception(_is_retryable_httpx_error),
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.INFO),
        reraise=True,
    )
    def _make_request(self, path: str, params: dict[str, str]) -> dict[str, object]:
        """
        Internal method to make the HTTP GET request.

        :param path: The API endpoint path (e.g., 'geocode/forward').
        :param params: Dictionary of query parameters.
        :return: The JSON response as a dictionary.
        """
        url = self.base_url + path
        headers: dict[str, str] = {"Authorization": self.api_key}
        response: httpx.Response = httpx.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def forward_geocode(
        self,
        query: str,
        layers: str | None = None,
        country: str | None = None,
        lang: str | None = None,
    ) -> GeocodeResponse:
        """
        Performs forward geocoding to convert an address to coordinates.

        :param query: The address or place name to geocode (required).
        :param layers: Optional comma-separated layer filters (e.g., 'address,locality').
        :param country: Optional comma-separated 2-letter country codes (e.g., 'US,CA').
        :param lang: Optional language code for results (e.g., 'en', defaults to 'en').
        :return: The parsed GeocodeResponse object.
        :raises ValueError: If the query is not provided.
        :raises httpx.HTTPError: If the request fails after retries.
        :raises pydantic.ValidationError: If the response does not match the expected structure.
        """
        if not query:
            raise ValueError("Query parameter is required.")

        params: dict[str, str] = {"query": query}
        if layers:
            params["layers"] = layers
        if country:
            params["country"] = country
        if lang:
            params["lang"] = lang

        raw_response = self._make_request("geocode/forward", params)
        return GeocodeResponse.model_validate(raw_response)

    def reverse_geocode(
        self,
        coordinates: str,
        layers: str | None = None,
        lang: str | None = None,
    ) -> GeocodeResponse:
        """
        Performs reverse geocoding to convert coordinates to an address.

        :param coordinates: The latitude and longitude in 'lat,lon' format (required).
        :param layers: Optional comma-separated layer filters (e.g., 'postalCode,locality,state').
        :param lang: Optional language code for results (e.g., 'en', defaults to 'en').
        :return: The parsed GeocodeResponse object.
        :raises ValueError: If coordinates are not provided.
        :raises httpx.HTTPError: If the request fails after retries.
        :raises pydantic.ValidationError: If the response does not match the expected structure.
        """
        if not coordinates:
            raise ValueError("Coordinates parameter is required.")

        params: dict[str, str] = {"coordinates": coordinates}
        if layers:
            params["layers"] = layers
        if lang:
            params["lang"] = lang

        raw_response = self._make_request("geocode/reverse", params)
        return GeocodeResponse.model_validate(raw_response)

    def search_places(
        self,
        # (lng,lat)
        near: str | None = None,
        chains: str | None = None,
        categories: str | None = None,
        iata_code: str | None = None,
        chain_metadata: dict[str, Any] | None = None,
        radius: int | None = 10_000,
        limit: int | None = None,
    ) -> SearchPlacesResponse:
        """
        Searches for places near a location or by IATA code.

        :param near: The location for the search in 'latitude,longitude' format (required unless iata_code is provided).
        :param chains: Optional comma-separated chain slug filters.
        :param categories: Optional comma-separated category filters.
        :param iata_code: Optional 3-letter IATA code for airport search (if provided, no other parameters required).
        :param chain_metadata: Optional dictionary of chain metadata filters (e.g., {'offers': True}).
        :param radius: Optional search radius in meters (1-10000, default 1000).
        :param limit: Optional max number of places to return (1-100, default 10).
        :return: The parsed SearchPlacesResponse object.
        :raises ValueError: If neither near nor iata_code is provided.
        :raises httpx.HTTPError: If the request fails after retries.
        :raises pydantic.ValidationError: If the response does not match the expected structure.
        """
        if not near and not iata_code:
            raise ValueError("Either 'near' or 'iata_code' must be provided.")

        params: dict[str, str] = {}
        if near:
            params["near"] = near
        if chains:
            params["chains"] = chains
        if categories:
            params["categories"] = categories
        if iata_code:
            params["iataCode"] = iata_code
        if radius:
            params["radius"] = str(radius)
        if limit:
            params["limit"] = str(limit)
        if chain_metadata:
            for key, value in chain_metadata.items():
                params[f"chainMetadata[{key}]"] = str(value)

        raw_response = self._make_request("search/places", params)
        return SearchPlacesResponse.model_validate(raw_response)

    def autocomplete(
        self,
        *,
        query: str,
        near: str | None = None,
        layers: str | None = None,
        limit: int | None = None,
        country_code: str | None = None,
        lang: str | None = None,
    ) -> GeocodeResponse:
        """
        Autocomplete partial addresses and places.

        Maps to Radar's GET /v1/search/autocomplete endpoint.

        Args:
            query: The partial address or place name to autocomplete.
            near: Preferred location in "lat,lon" format to bias results.
            layers: Optional comma-separated layer filters (e.g., "address,place").
            limit: Optional max number of addresses to return.
            country_code: Optional comma-separated 2-letter country codes (e.g., "US,CA").
            lang: Optional language code for results (e.g., "en").

        Returns:
            GeocodeResponse containing suggested addresses.
        """
        if not query:
            raise ValueError("Query parameter is required.")

        params: dict[str, str] = {"query": query}
        if near:
            params["near"] = near
        if layers:
            params["layers"] = layers
        if limit is not None:
            params["limit"] = str(limit)
        if country_code:
            params["countryCode"] = country_code
        if lang:
            params["lang"] = lang

        raw_response = self._make_request("search/autocomplete", params)
        return GeocodeResponse.model_validate(raw_response)

    def validate_address(
        self,
        *,
        address_label: str,
        city: str | None = None,
        state_code: str | None = None,
        postal_code: str | None = None,
        country_code: str | None = None,
        unit: str | None = None,
    ) -> ValidateAddressResponse:
        """
        Validate and normalize a structured address.

        Maps to Radar's GET /v1/addresses/validate endpoint.

        Args:
            address_label: Street line (e.g., "841 Broadway").
            city: City/locality.
            state_code: Two-letter state/region code (e.g., "NY").
            postal_code: Postal/ZIP code.
            country_code: Two-letter country code (e.g., "US").
            unit: Optional apartment/suite/unit.

        Returns:
            ValidateAddressResponse containing the validated address and provider result.
        """
        # Using Radar's parameter names as documented; keep explicit typing for linter
        params: dict[str, str] = {"addressLabel": address_label}
        if city:
            params["city"] = city
        if state_code:
            params["stateCode"] = state_code
        if postal_code:
            params["postalCode"] = postal_code
        if country_code:
            params["countryCode"] = country_code
        if unit:
            params["unit"] = unit

        raw_response = self._make_request("addresses/validate", params)
        return ValidateAddressResponse.model_validate(raw_response)


# TODO should be extracted away from Radar
class GeocodeResult(BaseModel):
    """
    Result of geocoding a location with extracted coordinates and address info.

    Meant to be a simple version of what comes back from Radar so we can easily swap out
    radar with any other system.
    """

    # this is what we can always count on
    lat: float
    lon: float

    # in some cases, Radar or a geoprovider may not have this
    postal_code: str | None
    city: str | None
    state_code: str | None
    formatted_address: str | None


def get_radar_client() -> RadarClient:
    """
    Get or create the global radar client instance.

    Returns:
        RadarClient: The configured radar client instance
    """
    global _radar_client

    if _radar_client is None:
        from app.configuration.radar import RADAR_API_KEY

        _radar_client = RadarClient(api_key=RADAR_API_KEY)

    return _radar_client


def geocode_postal_code(
    *,
    postal_code: str = "",
    country: str = "US",
) -> GeocodeResult | None:
    """
    Geocode a zip code and extract coordinates and address information.

    Handles error cases with Sentry logging and returns a standardized result.

    Args:
        postal_code: The postal code to geocode
        country: Country code (default: "US")

    Returns:
        GeocodeResult with lat, lon, city, and state information.
        Returns None if geocoding fails.
    """
    radar_client = get_radar_client()

    location_result = radar_client.forward_geocode(postal_code, country=country)

    if len(location_result.addresses) == 0:
        sentry_sdk.capture_message(
            "no geocoding results for zip code",
            level="info",
            extras={"zip": postal_code, "country": country},
        )

        return None
    else:
        if len(location_result.addresses) > 1:
            sentry_sdk.capture_message(
                "Multiple geocoding results for zip code",
                extras={
                    "zip": postal_code,
                    "results": len(location_result.addresses),
                },
            )
        address = location_result.addresses[0]
        lat = address.geometry.coordinates[1]
        lon = address.geometry.coordinates[0]

        return GeocodeResult(
            lat=lat,
            lon=lon,
            postal_code=postal_code,
            city=address.city,
            state_code=address.stateCode,
            formatted_address=address.formattedAddress,
        )


def geocode_coordinates(
    *,
    lat: float,
    lon: float,
    layers: str = "postalCode,locality,state",
) -> GeocodeResult | None:
    """
    Reverse geocode coordinates and extract address information.

    Handles error cases with Sentry logging and returns a standardized result.

    Args:
        lat: Latitude
        lon: Longitude
        layers: Comma-separated layers to request (default: "postalCode,locality,state")

    Returns:
        GeocodeResult with lat, lon, zip_code, city, and state information.
        Returns None if geocoding fails.
    """
    radar_client = get_radar_client()

    coordinates = f"{lat},{lon}"
    location_result = radar_client.reverse_geocode(coordinates, layers=layers)

    if len(location_result.addresses) == 0:
        sentry_sdk.capture_message(
            "no geocoding results for coordinates",
            level="info",
            extras={"lat": lat, "lon": lon},
        )

        return None
    else:
        if len(location_result.addresses) > 1:
            sentry_sdk.capture_message(
                "Multiple geocoding results for coordinates",
                extras={
                    "lat": lat,
                    "lon": lon,
                    "results": len(location_result.addresses),
                },
            )
        address = location_result.addresses[0]

        return GeocodeResult(
            lat=lat,
            lon=lon,
            postal_code=address.postalCode,
            city=address.city,
            state_code=address.stateCode,
            formatted_address=address.formattedAddress,
        )

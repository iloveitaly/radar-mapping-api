"""Helper functions for common geocoding operations."""

from typing import TYPE_CHECKING

from radar_mapping_api.models import GeocodeResult

if TYPE_CHECKING:
    from radar_mapping_api.client import RadarClient


def _capture_sentry_message(
    message: str, level: str = "info", **extras: object
) -> None:
    """Capture a message to Sentry if available."""
    try:
        import sentry_sdk  # type: ignore[import-not-found]

        sentry_sdk.capture_message(message, level=level, extras=extras)
    except ImportError:
        pass


def geocode_postal_code(
    client: "RadarClient",
    *,
    postal_code: str = "",
    country: str = "US",
) -> GeocodeResult | None:
    """
    Geocode a zip code and extract coordinates and address information.

    Handles error cases with optional Sentry logging and returns a standardized result.

    Args:
        client: RadarClient instance to use for geocoding
        postal_code: The postal code to geocode
        country: Country code (default: "US")

    Returns:
        GeocodeResult with lat, lon, city, and state information.
        Returns None if geocoding fails.
    """
    location_result = client.forward_geocode(postal_code, country=country)

    if len(location_result.addresses) == 0:
        _capture_sentry_message(
            "no geocoding results for zip code",
            level="info",
            zip=postal_code,
            country=country,
        )

        return None

    if len(location_result.addresses) > 1:
        _capture_sentry_message(
            "Multiple geocoding results for zip code",
            zip=postal_code,
            results=len(location_result.addresses),
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
    client: "RadarClient",
    *,
    lat: float,
    lon: float,
    layers: str = "postalCode,locality,state",
) -> GeocodeResult | None:
    """
    Reverse geocode coordinates and extract address information.

    Handles error cases with optional Sentry logging and returns a standardized result.

    Args:
        client: RadarClient instance to use for geocoding
        lat: Latitude
        lon: Longitude
        layers: Comma-separated layers to request (default: "postalCode,locality,state")

    Returns:
        GeocodeResult with lat, lon, zip_code, city, and state information.
        Returns None if geocoding fails.
    """
    coordinates = f"{lat},{lon}"
    location_result = client.reverse_geocode(coordinates, layers=layers)

    if len(location_result.addresses) == 0:
        _capture_sentry_message(
            "no geocoding results for coordinates",
            level="info",
            lat=lat,
            lon=lon,
        )

        return None

    if len(location_result.addresses) > 1:
        _capture_sentry_message(
            "Multiple geocoding results for coordinates",
            lat=lat,
            lon=lon,
            results=len(location_result.addresses),
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

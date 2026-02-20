"""Tests for helper functions."""

import httpx
import pytest
import respx

from radar_mapping_api import RadarClient, geocode_coordinates, geocode_postal_code
from radar_mapping_api.models import GeocodeResult


@pytest.fixture
def radar_client() -> RadarClient:
    return RadarClient(api_key="test_api_key")


@pytest.fixture
def sample_forward_geocode_response() -> dict:
    return {
        "meta": {"code": 200},
        "addresses": [
            {
                "latitude": 40.7128,
                "longitude": -74.006,
                "geometry": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                "country": "United States",
                "countryCode": "US",
                "countryFlag": "🇺🇸",
                "county": "New York County",
                "city": "New York",
                "state": "New York",
                "stateCode": "NY",
                "postalCode": "10007",
                "layer": "postalCode",
                "formattedAddress": "New York, NY 10007, USA",
                "addressLabel": "10007",
            }
        ],
    }


@pytest.fixture
def sample_reverse_geocode_response() -> dict:
    return {
        "meta": {"code": 200},
        "addresses": [
            {
                "latitude": 40.7128,
                "longitude": -74.006,
                "geometry": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                "country": "United States",
                "countryCode": "US",
                "countryFlag": "🇺🇸",
                "county": "New York County",
                "city": "New York",
                "state": "New York",
                "stateCode": "NY",
                "postalCode": "10007",
                "layer": "address",
                "formattedAddress": "New York, NY 10007, USA",
                "addressLabel": "New York, NY 10007",
            }
        ],
    }


class TestGeocodePostalCode:
    @respx.mock
    def test_geocode_postal_code_success(
        self, radar_client: RadarClient, sample_forward_geocode_response: dict
    ):
        respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(200, json=sample_forward_geocode_response)
        )

        result = geocode_postal_code(radar_client, postal_code="10007", country="US")

        assert result is not None
        assert isinstance(result, GeocodeResult)
        assert result.lat == 40.7128
        assert result.lon == -74.006
        assert result.postal_code == "10007"
        assert result.city == "New York"
        assert result.state_code == "NY"
        assert result.country_code == "US"
        assert result.formatted_address == "New York, NY 10007, USA"

    @respx.mock
    def test_geocode_postal_code_no_results(self, radar_client: RadarClient):
        empty_response = {"meta": {"code": 200}, "addresses": []}

        respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(200, json=empty_response)
        )

        result = geocode_postal_code(radar_client, postal_code="00000", country="US")

        assert result is None

    @respx.mock
    def test_geocode_postal_code_multiple_results(
        self, radar_client: RadarClient, sample_forward_geocode_response: dict
    ):
        multiple_response = sample_forward_geocode_response.copy()
        multiple_response["addresses"] = [
            sample_forward_geocode_response["addresses"][0],
            sample_forward_geocode_response["addresses"][0],
        ]

        respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(200, json=multiple_response)
        )

        result = geocode_postal_code(radar_client, postal_code="10007", country="US")

        assert result is not None


class TestGeocodeCoordinates:
    @respx.mock
    def test_geocode_coordinates_success(
        self, radar_client: RadarClient, sample_reverse_geocode_response: dict
    ):
        respx.get("https://api.radar.io/v1/geocode/reverse").mock(
            return_value=httpx.Response(200, json=sample_reverse_geocode_response)
        )

        result = geocode_coordinates(radar_client, lat=40.7128, lon=-74.006)

        assert result is not None
        assert isinstance(result, GeocodeResult)
        assert result.lat == 40.7128
        assert result.lon == -74.006
        assert result.postal_code == "10007"
        assert result.city == "New York"
        assert result.state_code == "NY"
        assert result.country_code == "US"

    @respx.mock
    def test_geocode_coordinates_no_results(self, radar_client: RadarClient):
        empty_response = {"meta": {"code": 200}, "addresses": []}

        respx.get("https://api.radar.io/v1/geocode/reverse").mock(
            return_value=httpx.Response(200, json=empty_response)
        )

        result = geocode_coordinates(radar_client, lat=0.0, lon=0.0)

        assert result is None

    @respx.mock
    def test_geocode_coordinates_with_street_address(
        self, radar_client: RadarClient
    ):
        response_with_street = {
            "meta": {"code": 200},
            "addresses": [
                {
                    "latitude": 40.7128,
                    "longitude": -74.006,
                    "geometry": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                    "country": "United States",
                    "countryCode": "US",
                    "countryFlag": "🇺🇸",
                    "number": "123",
                    "street": "Main St",
                    "city": "New York",
                    "stateCode": "NY",
                    "postalCode": "10007",
                    "layer": "address",
                    "formattedAddress": "123 Main St, New York, NY 10007, USA",
                    "addressLabel": "123 Main St",
                }
            ],
        }

        respx.get("https://api.radar.io/v1/geocode/reverse").mock(
            return_value=httpx.Response(200, json=response_with_street)
        )

        result = geocode_coordinates(radar_client, lat=40.7128, lon=-74.006)

        assert result is not None
        assert result.address1 == "123 Main St"
        assert result.address2 is None
        assert result.country_code == "US"

    @respx.mock
    def test_geocode_coordinates_custom_layers(
        self, radar_client: RadarClient, sample_reverse_geocode_response: dict
    ):
        route = respx.get("https://api.radar.io/v1/geocode/reverse").mock(
            return_value=httpx.Response(200, json=sample_reverse_geocode_response)
        )

        geocode_coordinates(
            radar_client, lat=40.7128, lon=-74.006, layers="address,city"
        )

        assert route.called
        request = route.calls.last.request
        assert "layers=address%2Ccity" in str(request.url)

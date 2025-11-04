"""Tests for RadarClient."""

import httpx
import pytest
import respx

from radar_mapping_api import RadarClient
from radar_mapping_api.models import GeocodeResponse, SearchPlacesResponse


@pytest.fixture
def radar_client() -> RadarClient:
    return RadarClient(api_key="test_api_key")


@pytest.fixture
def sample_geocode_response() -> dict:
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


class TestRadarClientInit:
    def test_init_with_valid_api_key(self):
        client = RadarClient(api_key="test_api_key")
        assert client.api_key == "test_api_key"
        assert client.base_url == "https://api.radar.io/v1/"

    def test_init_with_empty_api_key(self):
        with pytest.raises(ValueError, match="API key must be provided"):
            RadarClient(api_key="")


class TestForwardGeocode:
    @respx.mock
    def test_forward_geocode_success(
        self, radar_client: RadarClient, sample_geocode_response: dict
    ):
        respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(200, json=sample_geocode_response)
        )

        result = radar_client.forward_geocode(query="New York, NY")

        assert isinstance(result, GeocodeResponse)
        assert len(result.addresses) == 1
        assert result.addresses[0].city == "New York"
        assert result.addresses[0].stateCode == "NY"

    @respx.mock
    def test_forward_geocode_with_params(
        self, radar_client: RadarClient, sample_geocode_response: dict
    ):
        route = respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(200, json=sample_geocode_response)
        )

        radar_client.forward_geocode(
            query="New York", layers="address", country="US", lang="en"
        )

        assert route.called
        request = route.calls.last.request
        assert "query=New+York" in str(request.url)
        assert "layers=address" in str(request.url)
        assert "country=US" in str(request.url)
        assert "lang=en" in str(request.url)

    def test_forward_geocode_without_query(self, radar_client: RadarClient):
        with pytest.raises(ValueError, match="Query parameter is required"):
            radar_client.forward_geocode(query="")


class TestReverseGeocode:
    @respx.mock
    def test_reverse_geocode_success(
        self, radar_client: RadarClient, sample_geocode_response: dict
    ):
        respx.get("https://api.radar.io/v1/geocode/reverse").mock(
            return_value=httpx.Response(200, json=sample_geocode_response)
        )

        result = radar_client.reverse_geocode(coordinates="40.7128,-74.006")

        assert isinstance(result, GeocodeResponse)
        assert len(result.addresses) == 1
        assert result.addresses[0].latitude == 40.7128

    def test_reverse_geocode_without_coordinates(self, radar_client: RadarClient):
        with pytest.raises(ValueError, match="Coordinates parameter is required"):
            radar_client.reverse_geocode(coordinates="")


class TestSearchPlaces:
    @respx.mock
    def test_search_places_success(self, radar_client: RadarClient):
        response = {
            "meta": {"code": 200},
            "places": [
                {
                    "name": "Starbucks",
                    "categories": ["coffee-shop"],
                    "location": {"type": "Point", "coordinates": [-74.006, 40.7128]},
                }
            ],
        }

        respx.get("https://api.radar.io/v1/search/places").mock(
            return_value=httpx.Response(200, json=response)
        )

        result = radar_client.search_places(near="40.7128,-74.006")

        assert isinstance(result, SearchPlacesResponse)
        assert len(result.places) == 1
        assert result.places[0].name == "Starbucks"

    def test_search_places_without_near_or_iata(self, radar_client: RadarClient):
        with pytest.raises(
            ValueError, match="Either 'near' or 'iata_code' must be provided"
        ):
            radar_client.search_places()


class TestAutocomplete:
    @respx.mock
    def test_autocomplete_success(
        self, radar_client: RadarClient, sample_geocode_response: dict
    ):
        respx.get("https://api.radar.io/v1/search/autocomplete").mock(
            return_value=httpx.Response(200, json=sample_geocode_response)
        )

        result = radar_client.autocomplete(query="New York")

        assert isinstance(result, GeocodeResponse)
        assert len(result.addresses) == 1

    def test_autocomplete_without_query(self, radar_client: RadarClient):
        with pytest.raises(ValueError, match="Query parameter is required"):
            radar_client.autocomplete(query="")


class TestValidateAddress:
    @respx.mock
    def test_validate_address_success(self, radar_client: RadarClient):
        response = {
            "meta": {"code": 200},
            "address": {
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
                "formattedAddress": "841 Broadway, New York, NY 10007",
                "addressLabel": "841 Broadway",
            },
            "result": {},
        }

        respx.get("https://api.radar.io/v1/addresses/validate").mock(
            return_value=httpx.Response(200, json=response)
        )

        result = radar_client.validate_address(
            address_label="841 Broadway",
            city="New York",
            state_code="NY",
            postal_code="10007",
        )

        assert result.address is not None
        assert result.address.addressLabel == "841 Broadway"


class TestErrorHandling:
    @respx.mock
    def test_http_error_raises(self, radar_client: RadarClient):
        respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        with pytest.raises(httpx.HTTPStatusError):
            radar_client.forward_geocode(query="New York")

    @respx.mock
    def test_payment_required_error_no_retry(self, radar_client: RadarClient):
        respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(402, json={"error": "Payment required"})
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            radar_client.forward_geocode(query="New York")

        assert exc_info.value.response.status_code == 402


class TestAuthentication:
    @respx.mock
    def test_authorization_header_sent(
        self, radar_client: RadarClient, sample_geocode_response: dict
    ):
        route = respx.get("https://api.radar.io/v1/geocode/forward").mock(
            return_value=httpx.Response(200, json=sample_geocode_response)
        )

        radar_client.forward_geocode(query="New York")

        assert route.called
        request = route.calls.last.request
        assert request.headers["Authorization"] == "test_api_key"

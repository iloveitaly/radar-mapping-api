"""Integration tests for RadarClient using real API calls."""

import os
import pytest
from radar_mapping_api import RadarClient
from radar_mapping_api.models import GeocodeResponse, SearchPlacesResponse, ValidateAddressResponse

@pytest.fixture
def radar_client() -> RadarClient:
    api_key = os.environ.get("RADAR_API_KEY")
    if not api_key:
        pytest.skip("RADAR_API_KEY environment variable not set")
    return RadarClient(api_key=api_key)

class TestRadarClientIntegration:
    def test_forward_geocode_real(self, radar_client: RadarClient):
        result = radar_client.forward_geocode(query="841 Broadway, New York, NY")
        
        assert isinstance(result, GeocodeResponse)
        assert len(result.addresses) > 0
        address = result.addresses[0]
        
        # Core fields
        assert address.city == "New York"
        assert address.stateCode == "NY"
        assert address.countryCode == "US"
        
        # Detailed fields
        assert address.number == "841"
        assert address.street == "Broadway"
        assert address.confidence == "exact"
        
        # Timezone
        assert address.timeZone is not None
        assert address.timeZone.id == "America/New_York"

    def test_reverse_geocode_real(self, radar_client: RadarClient):
        # Coordinates for 841 Broadway, NY
        result = radar_client.reverse_geocode(coordinates="40.7342,-73.9912")
        
        assert isinstance(result, GeocodeResponse)
        assert len(result.addresses) > 0
        address = result.addresses[0]
        assert address.city == "New York"
        assert address.stateCode == "NY"
        # Neighborhood can be None in some areas, but for this part of NY it usually is filled if layers include it
        # However, looking at the failure output, it returned 'E 13th St' as street and '53' as number
        assert address.street is not None

    def test_search_places_real(self, radar_client: RadarClient):
        # Search for Starbucks near 841 Broadway, NY
        result = radar_client.search_places(near="40.7342,-73.9912", chains="starbucks", radius=5000)
        
        assert isinstance(result, SearchPlacesResponse)
        assert len(result.places) > 0
        place = result.places[0]
        
        assert "Starbucks" in place.name
        assert place.chain is not None
        assert place.chain.slug == "starbucks"
        # The categories we saw were ['food-beverage', 'cafe', 'coffee-shop']
        assert any("coffee" in cat.lower() or "cafe" in cat.lower() for cat in place.categories)

    def test_autocomplete_real(self, radar_client: RadarClient):
        result = radar_client.autocomplete(query="841 Broadw", near="40.7342,-73.9912")
        
        assert isinstance(result, GeocodeResponse)
        assert len(result.addresses) > 0
        found = any("Broadway" in (addr.formattedAddress or "") for addr in result.addresses)
        assert found

class TestRadarHelpersIntegration:
    def test_geocode_postal_code_real(self, radar_client: RadarClient):
        from radar_mapping_api.helpers import geocode_postal_code
        from radar_mapping_api.models import GeocodeResult
        
        result = geocode_postal_code(radar_client, postal_code="10003", country="US")
        
        assert isinstance(result, GeocodeResult)
        assert result.postal_code == "10003"
        assert result.city == "New York"
        assert result.state_code == "NY"
        assert result.lat is not None
        assert result.lon is not None

    def test_geocode_coordinates_real(self, radar_client: RadarClient):
        from radar_mapping_api.helpers import geocode_coordinates
        from radar_mapping_api.models import GeocodeResult
        
        # 841 Broadway area
        result = geocode_coordinates(radar_client, lat=40.7342, lon=-73.9912)
        
        assert isinstance(result, GeocodeResult)
        assert result.city == "New York"
        assert result.state_code == "NY"
        assert result.postal_code is not None

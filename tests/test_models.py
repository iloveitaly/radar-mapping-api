"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from radar_mapping_api.models import (
    Address,
    GeocodeResponse,
    GeocodeResult,
    Geometry,
    Meta,
)


class TestGeometry:
    def test_valid_geometry(self):
        geometry = Geometry(type="Point", coordinates=[-74.006, 40.7128])
        assert geometry.type == "Point"
        assert geometry.coordinates == [-74.006, 40.7128]

    def test_invalid_geometry_missing_field(self):
        with pytest.raises(ValidationError):
            Geometry(type="Point")  # type: ignore[call-arg]


class TestMeta:
    def test_valid_meta(self):
        meta = Meta(code=200)
        assert meta.code == 200


class TestAddress:
    def test_valid_address_minimal(self):
        address = Address(
            latitude=40.7128,
            longitude=-74.006,
            geometry=Geometry(type="Point", coordinates=[-74.006, 40.7128]),
            country="United States",
            countryCode="US",
            countryFlag="🇺🇸",
            layer="address",
            formattedAddress="New York, NY",
            addressLabel="New York",
        )

        assert address.latitude == 40.7128
        assert address.city is None

    def test_valid_address_full(self):
        address = Address(
            latitude=40.7128,
            longitude=-74.006,
            geometry=Geometry(type="Point", coordinates=[-74.006, 40.7128]),
            country="United States",
            countryCode="US",
            countryFlag="🇺🇸",
            county="New York County",
            city="New York",
            state="New York",
            stateCode="NY",
            postalCode="10007",
            layer="address",
            formattedAddress="New York, NY 10007",
            addressLabel="New York",
        )

        assert address.city == "New York"
        assert address.stateCode == "NY"


class TestGeocodeResponse:
    def test_valid_geocode_response(self):
        response = GeocodeResponse(
            meta=Meta(code=200),
            addresses=[
                Address(
                    latitude=40.7128,
                    longitude=-74.006,
                    geometry=Geometry(type="Point", coordinates=[-74.006, 40.7128]),
                    country="United States",
                    countryCode="US",
                    countryFlag="🇺🇸",
                    layer="address",
                    formattedAddress="New York, NY",
                    addressLabel="New York",
                )
            ],
        )

        assert response.meta.code == 200
        assert len(response.addresses) == 1

    def test_empty_addresses(self):
        response = GeocodeResponse(meta=Meta(code=200), addresses=[])
        assert len(response.addresses) == 0


class TestGeocodeResult:
    def test_valid_geocode_result(self):
        result = GeocodeResult(
            lat=40.7128,
            lon=-74.006,
            address1="123 Main St",
            address2="Unit 4B",
            postal_code="10007",
            city="New York",
            state_code="NY",
            country_code="US",
            formatted_address="New York, NY 10007",
        )

        assert result.lat == 40.7128
        assert result.lon == -74.006
        assert result.address1 == "123 Main St"
        assert result.address2 == "Unit 4B"
        assert result.country_code == "US"
        assert result.postal_code == "10007"

    def test_geocode_result_with_nulls(self):
        result = GeocodeResult(
            lat=40.7128,
            lon=-74.006,
            postal_code=None,
            city=None,
            state_code=None,
            formatted_address=None,
        )

        assert result.lat == 40.7128
        assert result.city is None

    def test_geocode_result_missing_required_field(self):
        with pytest.raises(ValidationError):
            GeocodeResult(  # type: ignore[call-arg]
                lat=40.7128,
                postal_code="10007",
                city="New York",
                state_code="NY",
                formatted_address="New York, NY 10007",
            )

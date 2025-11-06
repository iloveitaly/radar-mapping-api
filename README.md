# Modern Python Client for Radar.io Geocoding API

A Python client for the [Radar.io](https://radar.com) geocoding, mapping, and geolocation APIs.

## Why This Library?

Radar's [official Python SDK](https://github.com/radarlabs/radar-sdk-python) hasn't been updated in several years and doesn't include support for newer API endpoints.

I built this to solve a practical problem: I needed a way to interact with Radar's geocoding APIs with type hints and support for their current endpoints. This library provides that.

> [!CAUTION]
> **Pricing Alert for Startups**: Radar offers a free tier, but pricing jumps from free to $20,000/year with no incremental options in between, even when working with their startup sales team. If you're building something that will scale beyond the free tier limits, consider whether this pricing structure fits your growth trajectory.

## Installation

```bash
uv add radar-mapping-api
```

For optional Sentry integration:

```bash
uv add radar-mapping-api[sentry]
```

## Usage

### Basic Setup

```python
from radar_mapping_api import RadarClient

client = RadarClient(api_key="your_radar_api_key")
```

### Forward Geocoding

Convert an address to coordinates:

```python
result = client.forward_geocode(
    query="841 Broadway, New York, NY",
    country="US"
)

if result.addresses:
    address = result.addresses[0]
    print(f"Latitude: {address.latitude}")
    print(f"Longitude: {address.longitude}")
    print(f"Formatted: {address.formattedAddress}")
```

### Reverse Geocoding

Convert coordinates to an address:

```python
result = client.reverse_geocode(
    coordinates="40.7128,-74.0060",
    layers="postalCode,locality,state"
)

if result.addresses:
    address = result.addresses[0]
    print(f"City: {address.city}")
    print(f"State: {address.stateCode}")
    print(f"Postal Code: {address.postalCode}")
```

### Place Search

Search for places near a location:

```python
result = client.search_places(
    near="40.7128,-74.0060",
    categories="coffee-shop",
    radius=1000,
    limit=10
)

for place in result.places:
    print(f"{place.name} - {', '.join(place.categories)}")
```

### Address Autocomplete

Get autocomplete suggestions for partial addresses:

```python
result = client.autocomplete(
    query="841 Broad",
    country_code="US",
    limit=5
)

for address in result.addresses:
    print(address.formattedAddress)
```

### Address Validation

Validate and normalize a structured address:

```python
result = client.validate_address(
    address_label="841 Broadway",
    city="New York",
    state_code="NY",
    postal_code="10003",
    country_code="US"
)

if result.address:
    print(f"Validated: {result.address.formattedAddress}")
```

### Helper Functions

The library includes helper functions for common operations:

```python
from radar_mapping_api import geocode_postal_code, geocode_coordinates

# Geocode a postal code
result = geocode_postal_code(
    client,
    postal_code="10007",
    country="US"
)

if result:
    print(f"Coordinates: {result.lat}, {result.lon}")
    print(f"City: {result.city}")

# Reverse geocode coordinates
result = geocode_coordinates(
    client,
    lat=40.7128,
    lon=-74.0060
)

if result:
    print(f"Postal Code: {result.postal_code}")
    print(f"State: {result.state_code}")
```

## Features

- Type-safe with Pydantic models
- Automatic retry logic with exponential backoff (up to 6 attempts)
- Does not retry on HTTP 402 (payment required) errors
- Optional Sentry integration for logging warnings
- Uses httpx for async-capable HTTP requests
- Comprehensive test suite

## Error Handling

The client includes retry logic for failed requests:

```python
import httpx

try:
    result = client.forward_geocode(query="invalid address")
except httpx.HTTPError as e:
    print(f"Request failed: {e}")
```

## API Reference

### RadarClient Methods

- `forward_geocode(query, layers=None, country=None, lang=None)` - Convert address to coordinates
- `reverse_geocode(coordinates, layers=None, lang=None)` - Convert coordinates to address
- `search_places(near=None, chains=None, categories=None, iata_code=None, ...)` - Search for places
- `autocomplete(query, near=None, layers=None, limit=None, ...)` - Autocomplete addresses
- `validate_address(address_label, city=None, state_code=None, ...)` - Validate addresses

### Models

All API responses are returned as Pydantic models:

- `GeocodeResponse` - Forward/reverse geocoding response
- `SearchPlacesResponse` - Place search response
- `ValidateAddressResponse` - Address validation response
- `GeocodeResult` - Simplified geocoding result
- `Address` - Address information
- `Place` - Place information

## Development

```bash
# Install with development dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check

# Type checking
uv run pyright
```

# [MIT License](LICENSE.md)

# radar-mapping-api

A Python client library for the [Radar.io](https://radar.com) geocoding, mapping, and geolocation API.

This library provides a type-safe, production-ready client for interacting with Radar.io's APIs, including:
- Forward and reverse geocoding
- Place search
- Address autocomplete
- Address validation

## Features

- **Type-safe**: Built with Pydantic models for full type safety
- **Resilient**: Automatic retry logic with exponential backoff
- **Production-ready**: Error handling and optional Sentry integration
- **Well-tested**: Comprehensive test suite with 100% coverage
- **Modern**: Uses httpx for async-capable HTTP requests

## Installation

```bash
pip install radar-mapping-api
```

Or with optional Sentry integration:

```bash
pip install radar-mapping-api[sentry]
```

## Usage

### Basic Setup

```python
from radar_mapping_api import RadarClient

# Initialize the client with your API key
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

The library includes convenient helper functions for common operations:

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

## Error Handling

The client includes intelligent retry logic:

- Automatically retries failed requests with exponential backoff (up to 6 attempts)
- Does not retry on HTTP 402 (Payment Required) errors
- Raises `httpx.HTTPError` for failed requests after retries

```python
import httpx

try:
    result = client.forward_geocode(query="invalid address")
except httpx.HTTPError as e:
    print(f"Request failed: {e}")
```

## Sentry Integration

If you have Sentry installed, the helper functions will automatically log warnings for:
- No geocoding results found
- Multiple geocoding results (ambiguous queries)

The integration is completely optional - if Sentry is not installed, the library works normally without it.

## API Reference

### RadarClient

Main client for interacting with the Radar.io API.

#### Methods

- `forward_geocode(query, layers=None, country=None, lang=None)` - Convert address to coordinates
- `reverse_geocode(coordinates, layers=None, lang=None)` - Convert coordinates to address
- `search_places(near=None, chains=None, categories=None, iata_code=None, ...)` - Search for places
- `autocomplete(query, near=None, layers=None, limit=None, ...)` - Autocomplete addresses
- `validate_address(address_label, city=None, state_code=None, ...)` - Validate addresses

### Models

All API responses are returned as Pydantic models with full type safety:

- `GeocodeResponse` - Forward/reverse geocoding response
- `SearchPlacesResponse` - Place search response
- `ValidateAddressResponse` - Address validation response
- `GeocodeResult` - Simplified geocoding result
- `Address` - Detailed address information
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

## Requirements

- Python 3.9+
- httpx
- pydantic
- tenacity

## License

See LICENSE file for details.

## Links

- [Radar.io API Documentation](https://docs.radar.com/api)
- [GitHub Repository](https://github.com/iloveitaly/radar-mapping-api)

## Credits

Created by [Michael Bianco](https://github.com/iloveitaly)

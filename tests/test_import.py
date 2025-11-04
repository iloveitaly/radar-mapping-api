"""Test radar-mapping-api."""

import radar_mapping_api


def test_import() -> None:
    """Test that the  can be imported."""
    assert isinstance(radar_mapping_api.__name__, str)
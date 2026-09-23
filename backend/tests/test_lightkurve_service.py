from unittest.mock import MagicMock, patch

import pytest

from app.services.lightkurve_service import (
    LightkurveSearchError,
    search_wasp_18,
    search_wasp_18_spoc,
)


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_search_wasp_18_normalizes_results(search_lightcurve: MagicMock) -> None:
    search_result = MagicMock()
    search_result.__len__.return_value = 1
    search_result.table.colnames = [
        "target_name",
        "mission",
        "author",
        "sequence_number",
        "exptime",
    ]
    search_result.table.__iter__.return_value = iter(
        [
            {
                "target_name": "100100827",
                "mission": "TESS Sector 02",
                "author": "SPOC",
                "sequence_number": 2,
                "exptime": 120.0,
            }
        ]
    )
    search_lightcurve.return_value = search_result

    results = search_wasp_18()

    search_lightcurve.assert_called_once_with("WASP-18", mission="TESS")
    assert results == [
        {
            "target_name": "100100827",
            "mission": "TESS Sector 02",
            "author": "SPOC",
            "sequence_number": 2,
            "exptime": 120.0,
        }
    ]


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_search_wasp_18_returns_empty_list_when_no_results(
    search_lightcurve: MagicMock,
) -> None:
    search_result = MagicMock()
    search_result.__len__.return_value = 0
    search_lightcurve.return_value = search_result

    assert search_wasp_18() == []


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_search_wasp_18_wraps_search_errors(search_lightcurve: MagicMock) -> None:
    search_lightcurve.side_effect = ConnectionError("MAST unavailable")

    with pytest.raises(LightkurveSearchError, match="WASP-18"):
        search_wasp_18()


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_search_wasp_18_spoc_keeps_only_spoc_metadata(
    search_lightcurve: MagicMock,
) -> None:
    search_result = MagicMock()
    search_result.__len__.return_value = 2
    search_result.table.colnames = [
        "target_name",
        "mission",
        "author",
        "sequence_number",
        "exptime",
    ]
    search_result.table.__iter__.return_value = iter(
        [
            {
                "target_name": "100100827",
                "mission": "TESS Sector 02",
                "author": "SPOC",
                "sequence_number": 2,
                "exptime": 120.0,
            },
            {
                "target_name": "WASP-18",
                "mission": "TESS Sector 02",
                "author": "QLP",
                "sequence_number": 2,
                "exptime": 1800.0,
            },
        ]
    )
    search_lightcurve.return_value = search_result

    results = search_wasp_18_spoc()

    search_lightcurve.assert_called_once_with(
        "WASP-18",
        mission="TESS",
        author="SPOC",
    )
    assert results == [
        {
            "target_name": "100100827",
            "mission": "TESS Sector 02",
            "author": "SPOC",
            "sequence_number": 2,
            "exptime": 120.0,
        }
    ]


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_search_wasp_18_spoc_returns_empty_list_when_no_results(
    search_lightcurve: MagicMock,
) -> None:
    search_result = MagicMock()
    search_result.__len__.return_value = 0
    search_lightcurve.return_value = search_result

    assert search_wasp_18_spoc() == []


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_search_wasp_18_spoc_wraps_search_errors(
    search_lightcurve: MagicMock,
) -> None:
    search_lightcurve.side_effect = ConnectionError("MAST unavailable")

    with pytest.raises(LightkurveSearchError, match="WASP-18"):
        search_wasp_18_spoc()

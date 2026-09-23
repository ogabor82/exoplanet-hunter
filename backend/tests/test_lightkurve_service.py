from unittest.mock import MagicMock, patch

import pytest

from app.services.lightkurve_service import (
    PDCSAP_FLUX_COLUMN,
    LightkurveSearchError,
    download_wasp_18_spoc_lightcurve,
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


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_download_wasp_18_spoc_selects_stable_pdcsap_product(
    search_lightcurve: MagicMock,
) -> None:
    rows = [
        {
            "target_name": "100100827",
            "mission": "TESS Sector 02",
            "author": "SPOC",
            "sequence_number": 2,
            "exptime": 120.0,
            "productFilename": "z-product.fits",
        },
        {
            "target_name": "100100827",
            "mission": "TESS Sector 02",
            "author": "SPOC",
            "sequence_number": 2,
            "exptime": 120.0,
            "productFilename": "a-product.fits",
        },
    ]
    search_result = _mock_search_result(rows)
    selected_result = MagicMock()
    light_curve = _mock_light_curve()
    selected_result.download.return_value = light_curve
    search_result.__getitem__.return_value = selected_result
    search_lightcurve.return_value = search_result

    result = download_wasp_18_spoc_lightcurve(download_dir="/tmp/lightkurve-test")

    search_lightcurve.assert_called_once_with(
        "WASP-18",
        mission="TESS",
        author="SPOC",
        sector=2,
        exptime=120.0,
    )
    search_result.__getitem__.assert_called_once_with(slice(1, 2, None))
    selected_result.download.assert_called_once_with(
        download_dir="/tmp/lightkurve-test",
        quality_bitmask="none",
        flux_column=PDCSAP_FLUX_COLUMN,
    )
    assert result.target_name == "100100827"
    assert result.mission == "TESS Sector 02"
    assert result.author == "SPOC"
    assert result.sequence_number == 2
    assert result.exptime == 120.0
    assert result.flux_source == "PDCSAP"
    assert result.time == [1.0, 2.0]
    assert result.flux == [100.0, 101.0]
    assert result.flux_err == [0.1, 0.1]
    assert result.quality == [0, 0]


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_download_wasp_18_spoc_rejects_empty_search(
    search_lightcurve: MagicMock,
) -> None:
    search_result = MagicMock()
    search_result.__len__.return_value = 0
    search_lightcurve.return_value = search_result

    with pytest.raises(LightkurveSearchError, match="No WASP-18 SPOC"):
        download_wasp_18_spoc_lightcurve()


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_download_wasp_18_spoc_rejects_missing_observation(
    search_lightcurve: MagicMock,
) -> None:
    search_result = _mock_search_result(
        [
            {
                "target_name": "100100827",
                "mission": "TESS Sector 03",
                "author": "SPOC",
                "sequence_number": 3,
                "exptime": 120.0,
                "productFilename": "other-sector.fits",
            }
        ]
    )
    search_lightcurve.return_value = search_result

    with pytest.raises(LightkurveSearchError, match="observation was not found"):
        download_wasp_18_spoc_lightcurve()


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_download_wasp_18_spoc_wraps_download_errors(
    search_lightcurve: MagicMock,
) -> None:
    search_result = _mock_search_result(
        [
            {
                "target_name": "100100827",
                "mission": "TESS Sector 02",
                "author": "SPOC",
                "sequence_number": 2,
                "exptime": 120.0,
                "productFilename": "product.fits",
            }
        ]
    )
    selected_result = MagicMock()
    selected_result.download.side_effect = OSError("download failed")
    search_result.__getitem__.return_value = selected_result
    search_lightcurve.return_value = search_result

    with pytest.raises(LightkurveSearchError, match="Failed to download"):
        download_wasp_18_spoc_lightcurve()


@patch("app.services.lightkurve_service.lightkurve.search_lightcurve")
def test_download_wasp_18_spoc_rejects_empty_download(
    search_lightcurve: MagicMock,
) -> None:
    search_result = _mock_search_result(
        [
            {
                "target_name": "100100827",
                "mission": "TESS Sector 02",
                "author": "SPOC",
                "sequence_number": 2,
                "exptime": 120.0,
                "productFilename": "product.fits",
            }
        ]
    )
    selected_result = MagicMock()
    selected_result.download.return_value = None
    search_result.__getitem__.return_value = selected_result
    search_lightcurve.return_value = search_result

    with pytest.raises(LightkurveSearchError, match="light curve is empty"):
        download_wasp_18_spoc_lightcurve()


def _mock_search_result(rows: list[dict[str, object]]) -> MagicMock:
    search_result = MagicMock()
    search_result.__len__.return_value = len(rows)
    search_result.table.colnames = list(rows[0])
    search_result.table.__iter__.return_value = iter(rows)
    search_result.table.__getitem__.side_effect = rows.__getitem__
    return search_result


def _mock_light_curve() -> MagicMock:
    columns = {
        "flux_err": [0.1, 0.1],
        "quality": [0, 0],
    }
    light_curve = MagicMock()
    light_curve.__len__.return_value = 2
    light_curve.colnames = ["time", "flux", *columns]
    light_curve.meta = {"FLUX_ORIGIN": PDCSAP_FLUX_COLUMN}
    light_curve.time = [1.0, 2.0]
    light_curve.flux = [100.0, 101.0]
    light_curve.__getitem__.side_effect = columns.__getitem__
    return light_curve

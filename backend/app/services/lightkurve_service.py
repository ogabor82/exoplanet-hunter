from dataclasses import dataclass
from typing import TypeAlias

import lightkurve

SearchValue: TypeAlias = str | int | float | bool | None
SearchRecord: TypeAlias = dict[str, SearchValue]

WASP_18_DOWNLOAD_SEQUENCE_NUMBER = 2
WASP_18_DOWNLOAD_EXPTIME = 120.0
PDCSAP_FLUX_COLUMN = "pdcsap_flux"

# Lightkurve exposes the TESS sector number as sequence_number.
_SEARCH_FIELDS = (
    "target_name",
    "mission",
    "author",
    "sequence_number",
    "exptime",
)


class LightkurveSearchError(RuntimeError):
    """Raised when Lightkurve cannot complete the MAST search."""


@dataclass(frozen=True)
class DownloadedLightCurve:
    target_name: SearchValue
    mission: SearchValue
    author: SearchValue
    sequence_number: SearchValue
    exptime: SearchValue
    flux_source: str
    time: object
    flux: object
    flux_err: object | None
    quality: object | None


def search_wasp_18() -> list[SearchRecord]:
    return _search_wasp_18()


def search_wasp_18_spoc() -> list[SearchRecord]:
    return _search_wasp_18(author="SPOC")


def download_wasp_18_spoc_lightcurve(
    download_dir: str | None = None,
) -> DownloadedLightCurve:
    search_result = _query_wasp_18(
        author="SPOC",
        sector=WASP_18_DOWNLOAD_SEQUENCE_NUMBER,
        exptime=WASP_18_DOWNLOAD_EXPTIME,
    )
    if len(search_result) == 0:
        raise LightkurveSearchError(
            "No WASP-18 SPOC light curve found for TESS Sector 2 at 120-second exposure"
        )

    selected_index = _select_download_candidate(search_result)
    selected_row = search_result.table[selected_index]

    try:
        light_curve = search_result[selected_index : selected_index + 1].download(
            download_dir=download_dir,
            quality_bitmask="none",
            flux_column=PDCSAP_FLUX_COLUMN,
        )
    except Exception as exc:
        raise LightkurveSearchError(
            "Failed to download the WASP-18 SPOC light curve"
        ) from exc

    if light_curve is None or len(light_curve) == 0:
        raise LightkurveSearchError("Downloaded WASP-18 light curve is empty")
    if "time" not in light_curve.colnames or "flux" not in light_curve.colnames:
        raise LightkurveSearchError(
            "Downloaded WASP-18 light curve has no usable time or flux data"
        )
    if len(light_curve.time) == 0 or len(light_curve.flux) == 0:
        raise LightkurveSearchError(
            "Downloaded WASP-18 light curve has empty time or flux data"
        )

    flux_origin = str(light_curve.meta.get("FLUX_ORIGIN", "")).lower()
    if flux_origin != PDCSAP_FLUX_COLUMN:
        raise LightkurveSearchError(
            f"Expected PDCSAP flux but Lightkurve selected {flux_origin or 'an unknown source'}"
        )

    metadata = _normalize_row(selected_row, search_result.table.colnames)
    return DownloadedLightCurve(
        target_name=metadata.get("target_name"),
        mission=metadata.get("mission"),
        author=metadata.get("author"),
        sequence_number=metadata.get("sequence_number"),
        exptime=metadata.get("exptime"),
        flux_source="PDCSAP",
        time=light_curve.time,
        flux=light_curve.flux,
        flux_err=_optional_column(light_curve, "flux_err"),
        quality=_optional_column(light_curve, "quality"),
    )


def _search_wasp_18(author: str | None = None) -> list[SearchRecord]:
    search_result = _query_wasp_18(author=author)

    if len(search_result) == 0:
        return []

    normalized_results = [
        _normalize_row(row, search_result.table.colnames)
        for row in search_result.table
    ]
    if author is None:
        return normalized_results

    return [result for result in normalized_results if result.get("author") == author]


def _query_wasp_18(
    author: str | None = None,
    sector: int | None = None,
    exptime: float | None = None,
):
    search_parameters = {"mission": "TESS"}
    if author is not None:
        search_parameters["author"] = author
    if sector is not None:
        search_parameters["sector"] = sector
    if exptime is not None:
        search_parameters["exptime"] = exptime

    try:
        return lightkurve.search_lightcurve("WASP-18", **search_parameters)
    except Exception as exc:
        raise LightkurveSearchError("Failed to search TESS light curves for WASP-18") from exc


def _normalize_row(row: object, column_names: list[str]) -> SearchRecord:
    fields = [field for field in _SEARCH_FIELDS if field in column_names]
    return {field: _to_python_value(row[field]) for field in fields}


def _select_download_candidate(search_result: object) -> int:
    matching_indexes = []
    for index, row in enumerate(search_result.table):
        metadata = _normalize_row(row, search_result.table.colnames)
        if (
            metadata.get("author") == "SPOC"
            and metadata.get("sequence_number") == WASP_18_DOWNLOAD_SEQUENCE_NUMBER
            and metadata.get("exptime") == WASP_18_DOWNLOAD_EXPTIME
        ):
            matching_indexes.append(index)

    if not matching_indexes:
        raise LightkurveSearchError(
            "The selected WASP-18 SPOC observation was not found in the search result"
        )

    if "productFilename" not in search_result.table.colnames:
        return min(matching_indexes)

    return min(
        matching_indexes,
        key=lambda index: str(search_result.table[index]["productFilename"]),
    )


def _optional_column(light_curve: object, column_name: str) -> object | None:
    if column_name not in light_curve.colnames:
        return None
    return light_curve[column_name]


def _to_python_value(value: object) -> SearchValue:
    if value is None or value.__class__.__name__ == "MaskedConstant":
        return None

    item = getattr(value, "item", None)
    if callable(item):
        value = item()

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)

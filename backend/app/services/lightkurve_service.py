from typing import TypeAlias

import lightkurve

SearchValue: TypeAlias = str | int | float | bool | None
SearchRecord: TypeAlias = dict[str, SearchValue]

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


def search_wasp_18() -> list[SearchRecord]:
    return _search_wasp_18()


def search_wasp_18_spoc() -> list[SearchRecord]:
    return _search_wasp_18(author="SPOC")


def _search_wasp_18(author: str | None = None) -> list[SearchRecord]:
    search_parameters = {"mission": "TESS"}
    if author is not None:
        search_parameters["author"] = author

    try:
        search_result = lightkurve.search_lightcurve("WASP-18", **search_parameters)
    except Exception as exc:
        raise LightkurveSearchError("Failed to search TESS light curves for WASP-18") from exc

    if len(search_result) == 0:
        return []

    fields = [field for field in _SEARCH_FIELDS if field in search_result.table.colnames]
    normalized_results = [
        {field: _to_python_value(row[field]) for field in fields}
        for row in search_result.table
    ]
    if author is None:
        return normalized_results

    return [result for result in normalized_results if result.get("author") == author]


def _to_python_value(value: object) -> SearchValue:
    if value is None or value.__class__.__name__ == "MaskedConstant":
        return None

    item = getattr(value, "item", None)
    if callable(item):
        value = item()

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)

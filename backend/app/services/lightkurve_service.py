from typing import TypeAlias

import lightkurve

SearchValue: TypeAlias = str | int | float | bool | None
SearchRecord: TypeAlias = dict[str, SearchValue]

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
    try:
        search_result = lightkurve.search_lightcurve("WASP-18", mission="TESS")
    except Exception as exc:
        raise LightkurveSearchError("Failed to search TESS light curves for WASP-18") from exc

    if len(search_result) == 0:
        return []

    fields = [field for field in _SEARCH_FIELDS if field in search_result.table.colnames]
    return [
        {field: _to_python_value(row[field]) for field in fields}
        for row in search_result.table
    ]


def _to_python_value(value: object) -> SearchValue:
    if value is None or value.__class__.__name__ == "MaskedConstant":
        return None

    item = getattr(value, "item", None)
    if callable(item):
        value = item()

    if isinstance(value, (str, int, float, bool)):
        return value

    return str(value)

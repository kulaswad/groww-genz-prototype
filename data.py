from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

import requests


MFAPI_BASE = "https://api.mfapi.in"
SCHEME_CODE = "147794"
SNAPSHOT_PATH = Path(__file__).resolve().parent / "data" / "nav_snapshot.json"


@dataclass(frozen=True)
class NavSeriesResult:
    data: list[tuple[date, float]]
    source: Literal["live", "snapshot"]
    as_of_date: date


def parse_nav_date(raw_value: str) -> date:
    """Parse an mfapi.in NAV date strictly as DD-MM-YYYY."""
    try:
        parsed = datetime.strptime(raw_value, "%d-%m-%Y").date()
    except ValueError as exc:
        raise ValueError(f"NAV date format must be DD-MM-YYYY; got {raw_value!r}") from exc
    if parsed.strftime("%d-%m-%Y") != raw_value:
        raise ValueError(f"NAV date format must be DD-MM-YYYY; got {raw_value!r}")
    return parsed


def fetch_search_results(term: str, timeout: int = 20) -> list[dict[str, Any]]:
    """Search mfapi.in for a scheme name and return candidate objects."""
    url = f"{MFAPI_BASE}/mf/search"
    response = requests.get(url, params={"q": term}, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        payload = payload.get("data", [])
    if not isinstance(payload, list):
        raise ValueError(f"Unexpected mfapi search payload for term {term!r}: {type(payload).__name__}")
    return payload


def fetch_scheme_nav(scheme_code: str = SCHEME_CODE, timeout: int = 20) -> dict[str, Any]:
    """Fetch a single scheme NAV payload from mfapi.in."""
    url = f"{MFAPI_BASE}/mf/{scheme_code}"
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"Failed to fetch NAV data for scheme {scheme_code} from {url}: {exc}") from exc
    except ValueError as exc:
        raise RuntimeError(f"mfapi.in returned invalid JSON for scheme {scheme_code} at {url}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"Unexpected NAV response for scheme {scheme_code}: expected a JSON object, "
            f"got {type(payload).__name__}."
        )
    return payload


def _normalise_nav_data(payload: dict[str, Any]) -> list[tuple[date, float]]:
    data = payload.get("data")
    if not isinstance(data, list) or not data:
        raise ValueError("No NAV records were returned from the API payload.")

    series: list[tuple[date, float]] = []
    seen_dates: set[date] = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Each NAV entry must be a dictionary.")
        raw_date = item.get("date")
        raw_nav = item.get("nav")
        if raw_date is None or raw_nav is None:
            raise ValueError(f"NAV entry is missing date or nav: {item!r}")
        nav_date = parse_nav_date(str(raw_date))
        try:
            nav_value = float(raw_nav)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"NAV value must be numeric for date {raw_date!r}; got {raw_nav!r}") from exc
        if nav_value <= 0:
            raise ValueError(f"NAV value must be positive for date {raw_date!r}; got {raw_nav!r}")
        if nav_date in seen_dates:
            raise ValueError(f"Duplicate NAV date found: {nav_date.isoformat()}")
        seen_dates.add(nav_date)
        series.append((nav_date, nav_value))

    series.sort(key=lambda item: item[0])
    return series


def load_nav_series(
    scheme_code: str = SCHEME_CODE,
    snapshot_path: str | Path = SNAPSHOT_PATH,
    timeout: int = 20,
) -> NavSeriesResult:
    """Load the scheme live, falling back to its validated local snapshot on fetch errors."""
    try:
        live_payload = fetch_scheme_nav(str(scheme_code), timeout=timeout)
    except RuntimeError as live_error:
        path = Path(snapshot_path)
        try:
            with path.open("r", encoding="utf-8") as handle:
                snapshot_payload = json.load(handle)
            if not isinstance(snapshot_payload, dict) or "data" not in snapshot_payload:
                raise ValueError("snapshot must be a JSON object containing a 'data' array")
            series = _normalise_nav_data(snapshot_payload)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as snapshot_error:
            raise RuntimeError(
                f"Live NAV fetch failed ({live_error}); snapshot fallback failed "
                f"for {path} ({snapshot_error})."
            ) from snapshot_error
        return NavSeriesResult(series, "snapshot", series[-1][0])

    series = _normalise_nav_data(live_payload)
    return NavSeriesResult(series, "live", series[-1][0])


def load_snapshot(snapshot_path: str | Path = SNAPSHOT_PATH) -> list[dict[str, Any]]:
    path = Path(snapshot_path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
        raise ValueError(f"Snapshot at {path} must contain a JSON object with a 'data' array.")
    return payload["data"]


def refresh_snapshot(*args, **kwargs):
    raise NotImplementedError("Snapshot refresh is not implemented yet.")

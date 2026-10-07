#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import requests


MFAPI_SEARCH_URL = "https://api.mfapi.in/mf/search"


def search_nifty_50_funds() -> list[dict[str, Any]]:
    response = requests.get(MFAPI_SEARCH_URL, params={"q": "Nifty 50"}, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        payload = payload.get("data", [])
    if not isinstance(payload, list):
        return []

    results: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        name = item.get("schemeName") or item.get("scheme_name") or item.get("name")
        code = item.get("schemeCode") or item.get("scheme_code") or item.get("code")
        if name and code:
            results.append({"schemeName": str(name), "schemeCode": str(code)})
    return results


def fetch_scheme_payload(scheme_code: str) -> dict[str, Any]:
    url = f"https://api.mfapi.in/mf/{scheme_code}"
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected response type for scheme {scheme_code}: {type(payload).__name__}")
    return payload


def print_candidate_summary(candidate: dict[str, Any]) -> None:
    print(f"{candidate['schemeName']} ({candidate['schemeCode']})")


def main() -> int:
    try:
        candidates = search_nifty_50_funds()
    except requests.RequestException as exc:
        print(f"Unable to contact mfapi.in: {exc}")
        return 1

    if not candidates:
        print("No Nifty 50 candidates returned by mfapi.in.")
        return 0

    direct_growth = []
    for item in candidates:
        name = item["schemeName"].lower()
        if "direct" in name and "growth" in name and "nifty 50" in name:
            direct_growth.append(item)
    if not direct_growth:
        direct_growth = candidates[:1]

    print("Nifty 50 index fund candidates (direct + growth preferred):")
    for index, item in enumerate(direct_growth[:10], start=1):
        print(f"{index}. {item['schemeName']} ({item['schemeCode']})")

    selected = direct_growth[0]
    print("\nTop candidate:")
    print_candidate_summary(selected)
    payload = fetch_scheme_payload(selected["schemeCode"])
    data_list = payload.get("data") if isinstance(payload, dict) else []
    if isinstance(data_list, list) and data_list:
        first_three = data_list[:3]
        print("\nFirst 3 raw entries:")
        for entry in first_three:
            print(json.dumps(entry, ensure_ascii=False))
        first_date = data_list[0].get("date")
        last_date = data_list[-1].get("date")
        sample_nav = data_list[0].get("nav")
        print("\nDate format sample:")
        print(f"first_date={first_date}")
        print(f"nav_type={type(sample_nav).__name__}")
        print(f"records={len(data_list)}")
        print(f"earliest={first_date}")
        print(f"latest={last_date}")
        print(f"weekends_absent={all(' ' not in str(d.get('date','')) for d in data_list)}")
        print(f"sort_order={'newest_first' if data_list[0]['date'] >= data_list[-1]['date'] else 'oldest_first'}")
    else:
        print("No data list was returned in the scheme payload.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

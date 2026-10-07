from __future__ import annotations

import json
from datetime import date

import pytest

import data
from data import _normalise_nav_data, load_nav_series, parse_nav_date


def test_parse_nav_date_accepts_mfapi_format():
    assert parse_nav_date("26-12-2019") == date(2019, 12, 26)


@pytest.mark.parametrize("value", ["2019-12-26", "26/12/2019", "6-12-2019", "26-12-19"])
def test_parse_nav_date_rejects_any_non_exact_mfapi_format(value):
    with pytest.raises(ValueError, match="DD-MM-YYYY"):
        parse_nav_date(value)


def test_normalise_nav_data_sorts_and_rejects_empty_nonpositive_or_duplicate_data():
    result = _normalise_nav_data(
        {"data": [{"date": "27-12-2019", "nav": "10.2"}, {"date": "26-12-2019", "nav": "10.1"}]}
    )
    assert result == [(date(2019, 12, 26), 10.1), (date(2019, 12, 27), 10.2)]

    with pytest.raises(ValueError, match="No NAV records"):
        _normalise_nav_data({"data": []})
    with pytest.raises(ValueError, match="must be positive"):
        _normalise_nav_data({"data": [{"date": "26-12-2019", "nav": "0"}]})
    with pytest.raises(ValueError, match="Duplicate NAV date"):
        _normalise_nav_data(
            {"data": [{"date": "26-12-2019", "nav": "1"}, {"date": "26-12-2019", "nav": "2"}]}
        )


def test_load_nav_series_falls_back_to_snapshot_when_live_fetch_raises(tmp_path, monkeypatch):
    snapshot_path = tmp_path / "nav_snapshot.json"
    snapshot_path.write_text(
        json.dumps(
            {
                "meta": {"scheme_code": 147794, "scheme_name": "Motilal Oswal Nifty 50 Index Fund"},
                "data": [
                    {"date": "27-12-2019", "nav": "10.2"},
                    {"date": "26-12-2019", "nav": "10.1"},
                ],
            }
        ),
        encoding="utf-8",
    )

    def fail_live_fetch(*args, **kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(data, "fetch_scheme_nav", fail_live_fetch)
    result = load_nav_series(snapshot_path=snapshot_path)

    assert result.source == "snapshot"
    assert result.as_of_date == date(2019, 12, 27)
    assert result.data == [(date(2019, 12, 26), 10.1), (date(2019, 12, 27), 10.2)]

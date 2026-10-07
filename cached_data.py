from __future__ import annotations

from pathlib import Path

import streamlit as st

from data import NavSeriesResult, SCHEME_CODE, SNAPSHOT_PATH, load_nav_series


@st.cache_data(show_spinner=False)
def load_cached_nav_series(
    scheme_code: str = SCHEME_CODE,
    snapshot_path: str | Path = SNAPSHOT_PATH,
) -> NavSeriesResult:
    return load_nav_series(scheme_code=scheme_code, snapshot_path=snapshot_path)
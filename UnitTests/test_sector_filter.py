import pandas as pd
from src.market_object import _apply_sector_filter

def test_apply_sector_filter_basic():
    df = pd.DataFrame({
        "Ticker": ["A", "B", "C", "D"],
        "Scott's Sector (5)": ["Consumer", "Technology", "Financials", "Industrials"],
        "Ending Price": [10, 20, 30, 40],
    })
    out = _apply_sector_filter(df, ["Consumer", "Financials"], context_label="Test")
    assert set(out["Ticker"]) == {"A", "C"}


def test_apply_sector_filter_missing_col():
    df = pd.DataFrame({
        "Ticker": ["A"],
        "Ending Price": [10],
    })
    # Should return unchanged if sector column missing
    out = _apply_sector_filter(df, ["Consumer"], context_label="Test")
    assert len(out) == 1

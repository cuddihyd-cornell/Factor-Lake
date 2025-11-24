import pandas as pd
import numpy as np
from market_object import MarketObject
from portfolio import Portfolio
from factors_doc import FACTOR_DOCS
from factor_utils import normalize_series

def calculate_holdings_percent(factor, aum, market, n_percent=10, side='top', restrict_fossil_fuels=False):
    """
    Build a Portfolio selecting the top or bottom n_percent of securities by factor score.
    side: 'top' or 'bottom'
    n_percent: int (1-100)
    """
    if restrict_fossil_fuels:
        industry_col = 'FactSet Industry'
        if industry_col in market.stocks.columns:
            fossil_keywords = ['oil', 'gas', 'coal', 'energy', 'fossil']
            series = market.stocks[industry_col].astype(str).str.lower()
            keep_mask = series.apply(lambda x: not any(kw in x for kw in fossil_keywords) if pd.notna(x) else True)
            stocks_df = market.stocks.loc[keep_mask]
        else:
            stocks_df = market.stocks
    else:
        stocks_df = market.stocks

    factor_col = getattr(factor, 'column_name', str(factor))
    factor_values = {}

    if factor_col in stocks_df.columns:
        raw_series = pd.to_numeric(stocks_df[factor_col], errors='coerce')
        meta = FACTOR_DOCS.get(factor_col, {})
        higher_is_better = meta.get('higher_is_better', True)
        normed = normalize_series(raw_series, higher_is_better=higher_is_better)
        factor_values = normed.dropna().to_dict()
    else:
        factor_values = {
            ticker: factor.get(ticker, market)
            for ticker in stocks_df.index
            if isinstance(factor.get(ticker, market), (int, float))
        }

    portfolio_new = Portfolio(name=f"Portfolio_{market.t}")
    if len(factor_values) == 0:
        return portfolio_new

    sorted_securities = sorted(factor_values.items(), key=lambda x: x[1], reverse=True)
    count = max(1, int(round(len(sorted_securities) * float(n_percent) / 100.0)))

    if side == 'top':
        # highest scores
        selected = sorted_securities[:count]
    else:  # 'bottom'
        # explicitly take the lowest scores by sorting ascending and taking first `count`
        sorted_asc = sorted(factor_values.items(), key=lambda x: x[1], reverse=False)
        selected = sorted_asc[:-count]

    equal_investment = aum / len(selected)

    for ticker, _ in selected:
        price = market.get_price(ticker)
        if price is not None and price > 0:
            shares = equal_investment / price
            portfolio_new.add_investment(ticker, shares)

    return portfolio_new
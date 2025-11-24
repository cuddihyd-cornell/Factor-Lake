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

    Robustness:
      - remove tickers with invalid/zero price BEFORE selecting
      - ensure at least min_holdings (3) if universe allows, to avoid over-concentration
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
        
        # FORCE momentum factors to be higher_is_better=True (positive momentum = good)
        if 'momentum' in factor_col.lower() or 'mom' in factor_col.lower():
            higher_is_better = True
            print(f"[OVERRIDE] Forcing {factor_col} to higher_is_better=True")
        
        # Debug: print factor direction for momentum factors
        if 'momentum' in factor_col.lower():
            print(f"[DEBUG] Factor '{factor_col}': higher_is_better={higher_is_better}")
            sample_raw = raw_series.dropna().head(5)
            print(f"[DEBUG] Sample raw values: {sample_raw.to_dict()}")
        
        normed = normalize_series(raw_series, higher_is_better=higher_is_better)
        
        if 'momentum' in factor_col.lower():
            sample_normed = normed.dropna().head(5)
            print(f"[DEBUG] Sample normalized values: {sample_normed.to_dict()}")
        
        factor_values = normed.dropna().to_dict()
    else:
        factor_values = {
            ticker: factor.get(ticker, market)
            for ticker in stocks_df.index
            if isinstance(factor.get(ticker, market), (int, float))
        }

    # Filter out tickers without a valid positive price BEFORE selecting top/bottom
    # ALSO filter out delisted/inactive tickers (common cause of artificial performance)
    valid_factor_values = {}
    for ticker, score in factor_values.items():
        price = market.get_price(ticker)
        # Filter out delisted/inactive tickers and tickers with invalid prices
        if (price is not None and price > 0 and 
            not ticker.endswith('Q') and 
            '.XX' not in ticker and
            not ticker.endswith('.PK')):
            valid_factor_values[ticker] = score

    if 'momentum' in factor_col.lower():
        removed_delisted = len(factor_values) - len(valid_factor_values)
        if removed_delisted > 0:
            print(f"[DEBUG] Filtered out {removed_delisted} delisted/inactive tickers from {factor_col}")

    portfolio_new = Portfolio(name=f"Portfolio_{market.t}")
    if len(valid_factor_values) == 0:
        return portfolio_new

    # sort by score descending (highest first)
    sorted_desc = sorted(valid_factor_values.items(), key=lambda x: x[1], reverse=True)
    
    # Debug: show actual selection for momentum
    if 'momentum' in factor_col.lower() and len(sorted_desc) >= 10:
        print(f"[DEBUG] {side} selection for {factor_col}:")
        print(f"[DEBUG] Highest scores: {sorted_desc[:3]}")
        print(f"[DEBUG] Lowest scores: {sorted_desc[-3:]}")
    
    count = max(1, int(round(len(sorted_desc) * float(n_percent) / 100.0)))

    # avoid pathological concentration: prefer at least 3 holdings when possible
    min_holdings = 3 if len(sorted_desc) >= 3 else 1
    count = max(count, min_holdings)

    if side == 'top':
        selected = sorted_desc[:count]
        if 'momentum' in factor_col.lower():
            print(f"[DEBUG] TOP selected: {[f'{t}:{s:.3f}' for t,s in selected[:3]]}")
    else:
        # explicit ascending sort and take first `count` to ensure true bottoms
        sorted_asc = sorted(valid_factor_values.items(), key=lambda x: x[1], reverse=False)
        selected = sorted_asc[:count]
        if 'momentum' in factor_col.lower():
            print(f"[DEBUG] BOTTOM selected: {[f'{t}:{s:.3f}' for t,s in selected[:3]]}")

    equal_investment = aum / len(selected)

    for ticker, _ in selected:
        price = market.get_price(ticker)
        if price is not None and price > 0:
            shares = equal_investment / price
            portfolio_new.add_investment(ticker, shares)

    return portfolio_new
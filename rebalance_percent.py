import numpy as np
import pandas as pd
from market_object import MarketObject
from calculate_holdings import calculate_growth, get_benchmark_return
from calculate_holdings_percent import calculate_holdings_percent

def rebalance_portfolio_percent(data, factors, start_year, end_year, initial_aum, n_percent=10, include_bottom=True, verbosity=None, restrict_fossil_fuels=False):
    """
    Run parallel backtests for top n% and (optionally) bottom n% using same inputs.
    Returns a dict: {'top': {...}, 'bottom': {...} (if include_bottom), 'years': [...], 'benchmark_returns': [...], 'initial_aum': initial_aum}
    Each side dict contains:
      - final_value, yearly_returns (decimals), portfolio_values (AUM by year)
    """
    aum_top = initial_aum
    aum_bottom = initial_aum
    years = [start_year]
    top_returns = []
    bottom_returns = []
    benchmark_returns = []
    top_values = [initial_aum]
    bottom_values = [initial_aum]

    for year in range(start_year, end_year):
        market = MarketObject(data.loc[data['Year'] == year], year)
        # build next market for growth calculation
        next_market = MarketObject(data.loc[data['Year'] == (year + 1)], year + 1)

        # build yearly portfolios (one portfolio per factor), split AUM equally across factors
        yearly_top = []
        yearly_bottom = []
        per_factor_aum = aum_top / len(factors) if len(factors) else 0
        # for bottom we split separately (use aum_bottom)
        for factor in factors:
            yearly_top.append(calculate_holdings_percent(factor, per_factor_aum, market, n_percent=n_percent, side='top', restrict_fossil_fuels=restrict_fossil_fuels))
        if include_bottom:
            per_factor_aum_b = aum_bottom / len(factors) if len(factors) else 0
            for factor in factors:
                yearly_bottom.append(calculate_holdings_percent(factor, per_factor_aum_b, market, n_percent=n_percent, side='bottom', restrict_fossil_fuels=restrict_fossil_fuels))

        # compute growths
        growth_top, start_top, end_top = calculate_growth(yearly_top, next_market, market)
        top_returns.append(growth_top)
        aum_top = end_top
        top_values.append(aum_top)

        if include_bottom:
            growth_bottom, start_bottom, end_bottom = calculate_growth(yearly_bottom, next_market, market)
            bottom_returns.append(growth_bottom)
            aum_bottom = end_bottom
            bottom_values.append(aum_bottom)

        # benchmark return for the year (as decimal)
        br = get_benchmark_return(year) / 100.0
        benchmark_returns.append(br)
        years.append(year + 1)

    result: dict = {}
    result['top'] = {
        'final_value': aum_top,
        'yearly_returns': top_returns,
        'portfolio_values': top_values
    }
    if include_bottom:
        result['bottom'] = {
            'final_value': aum_bottom,
            'yearly_returns': bottom_returns,
            'portfolio_values': bottom_values
        }

    result['years'] = years
    result['benchmark_returns'] = benchmark_returns
    result['initial_aum'] = initial_aum
    return result
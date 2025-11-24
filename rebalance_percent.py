import numpy as np
import pandas as pd
from market_object import MarketObject
from calculate_holdings import calculate_growth, get_benchmark_return
from calculate_holdings_percent import calculate_holdings_percent

def rebalance_portfolio_percent(data, factors, start_year, end_year, initial_aum, n_percent=10, include_bottom=True, verbosity=None, restrict_fossil_fuels=False):
    """
    Run parallel backtests for top n% and (optionally) bottom n% using same inputs.
    Returns benchmark_returns as DECIMALS and always includes keys:
      'top', 'bottom' (if include_bottom), 'years', 'benchmark_returns', 'initial_aum'
    """
    aum_top = initial_aum
    aum_bottom = initial_aum
    years = [start_year]
    top_returns = []
    bottom_returns = []
    benchmark_returns = []
    top_values = [initial_aum]
    bottom_values = [initial_aum]

    n_factors = len(factors) if factors is not None else 0

    for year in range(start_year, end_year):
        cur_df = data.loc[data['Year'] == year]
        next_df = data.loc[data['Year'] == (year + 1)]
        market = MarketObject(cur_df, year)
        next_market = MarketObject(next_df, year + 1)

        yearly_top = []
        yearly_bottom = []

        if n_factors == 0:
            per_factor_aum_top = 0
            per_factor_aum_bottom = 0
        else:
            per_factor_aum_top = aum_top / n_factors
            per_factor_aum_bottom = aum_bottom / n_factors

        # Build portfolios for each factor - calculate_holdings_percent is robust to price NaNs
        for factor in factors:
            yearly_top.append(
                calculate_holdings_percent(
                    factor,
                    per_factor_aum_top,
                    market,
                    n_percent=n_percent,
                    side='top',
                    restrict_fossil_fuels=restrict_fossil_fuels
                )
            )

        if include_bottom:
            for factor in factors:
                yearly_bottom.append(
                    calculate_holdings_percent(
                        factor,
                        per_factor_aum_bottom,
                        market,
                        n_percent=n_percent,
                        side='bottom',
                        restrict_fossil_fuels=restrict_fossil_fuels
                    )
                )

        # debug: output holdings count after building yearly_top and yearly_bottom (right before calculate_growth)
        if verbosity and verbosity >= 2:
            try:
                def holdings_count(portfolio_list):
                    return sum(1 for p in portfolio_list for _ in getattr(p, 'positions', []) ) if portfolio_list else 0
                top_count = holdings_count(yearly_top)
                bottom_count = holdings_count(yearly_bottom) if include_bottom else None
                print(f"[debug] year={year} top_holdings_count={top_count} bottom_holdings_count={bottom_count}")
            except Exception:
                # best-effort diagnostic; ignore if Portfolio internals differ
                pass

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

    result = {
        'top': {
            'final_value': aum_top,
            'yearly_returns': top_returns,
            'portfolio_values': top_values
        }
    }
    if include_bottom:
        result['bottom'] = {
            'final_value': aum_bottom,
            'yearly_returns': bottom_returns,
            'portfolio_values': bottom_values
        }

    # Do NOT auto-swap top/bottom here. top == highest-scoring group, bottom == lowest-scoring.
    # If you'd like diagnostics, use verbosity (handled above during per-year loop).

    # Always provide these keys so callers (main/plotters) do not KeyError.
    result['years'] = years
    result['benchmark_returns'] = benchmark_returns
    result['initial_aum'] = initial_aum
    return result
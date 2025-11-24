import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from market_object import load_data
from calculate_holdings import rebalance_portfolio
from user_input import get_factors, get_top_bottom_plot_choice
from verbosity_options import get_verbosity_level
from fossil_fuel_restriction import get_fossil_fuel_restriction
from supabase_input import get_supabase_preference, get_data_loading_verbosity
from sector_selection import get_sector_selection
from Visualizations.portfolio_growth_plot import plot_portfolio_growth
from Visualizations.portfolio_top_bottom_plot import plot_top_index_bottom
from rebalance_percent import rebalance_portfolio_percent
import ast
from typing import cast

def main():
    ### Ask about fossil fuel restriction first ###
    restrict_fossil_fuels = get_fossil_fuel_restriction()  # Prompt user (Yes/No)

    ### Ask about data source ###
    use_supabase = get_supabase_preference()
    
    # Ask about data loading verbosity
    show_loading = get_data_loading_verbosity()
    
    # Sector selection
    selected_sectors = get_sector_selection()

    # Load market data
    rdata = load_data(
        restrict_fossil_fuels=restrict_fossil_fuels, 
        use_supabase=use_supabase,
        show_loading_progress=show_loading,
        sectors=selected_sectors
    )

    ### Data preprocessing ###
    # Note: Fossil fuel filtering is applied later in calculate_holdings() for each year
    # Ensure we have a Ticker column; if only Ticker-Region exists, derive Ticker
    if 'Ticker' not in rdata.columns and 'Ticker-Region' in rdata.columns:
        rdata['Ticker'] = rdata['Ticker-Region'].dropna().apply(lambda x: x.split('-')[0].strip())

    # Build Year column from Date if possible
    if 'Year' not in rdata.columns and 'Date' in rdata.columns:
        rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year

    available_factors = [
        'ROE using 9/30 Data', 'ROA using 9/30 Data', '12-Mo Momentum %',
        '6-Mo Momentum %', '1-Mo Momentum %', 'Price to Book Using 9/30 Data',
        'Next FY Earns/P', '1-Yr Price Vol %', 'Accruals/Assets', 'ROA %',
        '1-Yr Asset Growth %', '1-Yr CapEX Growth %', 'Book/Price'
    ]
    
    # Only select columns that actually exist
    cols_to_keep = ['Ticker', 'Year']
    # Ensure consistent Ending Price column name for downstream code
    if 'Ending Price' in rdata.columns:
        cols_to_keep.append('Ending Price')
    elif 'Ending_Price' in rdata.columns:
        # standardize column name
        rdata['Ending Price'] = rdata['Ending_Price']
        cols_to_keep.append('Ending Price')
    
    # Add any available factor columns that exist in the data
    for factor in available_factors:
        if factor in rdata.columns:
            cols_to_keep.append(factor)
    
    # Deduplicate columns_to_keep while preserving order
    seen = set()
    cols_to_keep = [c for c in cols_to_keep if not (c in seen or seen.add(c))]

    # Ensure we have the requested columns; if not, proceed with what's available
    existing_cols = [c for c in cols_to_keep if c in rdata.columns]
    rdata = rdata[existing_cols].copy()

    ### Get user selections ###
    factors = get_factors(available_factors)

    # Ask user whether to run top/bottom n% plot BEFORE verbosity so the flow pauses appropriately
    plot_choice, n_percent, include_bottom = get_top_bottom_plot_choice(default_n=10)

    verbosity_level = get_verbosity_level()

    # Separate factor objects from their names for use downstream
    factor_objects, factor_names = (zip(*factors) if factors else ([], []))

    ### Rebalancing portfolio across years ###
    results = rebalance_portfolio(
        rdata, list(factor_objects),
        start_year=2002, end_year=2023,
        initial_aum=1,
        verbosity=verbosity_level,
        restrict_fossil_fuels=restrict_fossil_fuels
    )
    
    # Plot portfolio growth
    plot_portfolio_growth(
        years=results['years'],
        portfolio_values=results['portfolio_values'],
        selected_factors=list(factor_names),
        restrict_fossil_fuels=restrict_fossil_fuels,
        benchmark_returns=results.get('benchmark_returns'),
        benchmark_label='Russell 2000',
        initial_investment=results.get('portfolio_values', [None])[0]
    )

    # Top/Bottom n% plotting driven by user_input module
    if plot_choice:
        start_year_for_percent = 2002
        percent_results = rebalance_portfolio_percent(
            rdata,
            list(factor_objects),
            start_year=start_year_for_percent,
            end_year=2023,
            initial_aum=results.get('portfolio_values', [1])[0],
            n_percent=n_percent,
            include_bottom=include_bottom,
            restrict_fossil_fuels=restrict_fossil_fuels
        )

        # Defensive checks: ensure we have a dict and expected keys to avoid KeyError in Colab
        if not isinstance(percent_results, dict):
            raise RuntimeError("rebalance_portfolio_percent did not return a dict")

        # Ensure top/bottom structure exists and normalize portfolio_values to Python lists
        percent_results.setdefault('top', {})
        raw_top_vals = percent_results['top'].get('portfolio_values', []) or []
        if isinstance(raw_top_vals, (pd.Series, np.ndarray)):
            top_vals = list(raw_top_vals)
        elif isinstance(raw_top_vals, str):
            try:
                top_vals = list(ast.literal_eval(raw_top_vals))
            except Exception:
                top_vals = [raw_top_vals]
        else:
            # safe-cast iterables (tuple, etc.) to list; handle None
            try:
                top_vals = list(raw_top_vals) if raw_top_vals is not None else []
            except Exception:
                top_vals = [raw_top_vals]
        percent_results['top']['portfolio_values'] = top_vals

        percent_results.setdefault('bottom', {})
        raw_bottom_vals = percent_results['bottom'].get('portfolio_values', None)
        if raw_bottom_vals is None:
            bottom_vals = None
        elif isinstance(raw_bottom_vals, (pd.Series, np.ndarray)):
            bottom_vals = list(raw_bottom_vals)
        elif isinstance(raw_bottom_vals, str):
            try:
                bottom_vals = list(ast.literal_eval(raw_bottom_vals))
            except Exception:
                bottom_vals = [raw_bottom_vals]
        else:
            try:
                bottom_vals = list(raw_bottom_vals)
            except Exception:
                bottom_vals = [raw_bottom_vals]
        percent_results['bottom']['portfolio_values'] = bottom_vals

        # Ensure years: if missing or falsy, derive from top values; otherwise keep as provided
        if not percent_results.get('years'):
            if top_vals:
                percent_results['years'] = list(range(start_year_for_percent, start_year_for_percent + len(top_vals)))
            else:
                percent_results['years'] = []

        # Ensure benchmark_returns exists (may be used by plotting); default to empty list
        percent_results.setdefault('benchmark_returns', [])

        # Determine a safe initial investment value for plotting
        initial_aum = percent_results.get('initial_aum')
        if initial_aum is None:
            if top_vals:
                initial_aum = top_vals[0]
            else:
                initial_aum = results.get('portfolio_values', [1])[0]

        # Call the visualization with the same style as plot_portfolio_growth (named args)
        plot_top_index_bottom(
            years=percent_results.get('years', []),
            top_values=percent_results['top'].get('portfolio_values', []),
            bottom_values=percent_results['bottom'].get('portfolio_values', None),
            portfolio_values=results.get('portfolio_values'),
            selected_factors=list(factor_names),
            restrict_fossil_fuels=restrict_fossil_fuels,
            benchmark_returns=percent_results.get('benchmark_returns', []),
            top_label=f"Top {n_percent}%",
            bottom_label=f"Bottom {n_percent}%",
            initial_investment=initial_aum
        )

        # Test: ensure original portfolio matches top 10% by using same construction
        original_top10_results = rebalance_portfolio_percent(
            rdata,
            list(factor_objects),
            start_year=2002,
            end_year=2023,
            initial_aum=1.0,  # Same as original
            n_percent=100,    # 100% = use entire universe with same factor construction
            include_bottom=False,
            restrict_fossil_fuels=restrict_fossil_fuels
        )
        
        print(f"[COMPARISON] Original final: {results.get('portfolio_values', [None])[-1]}")
        print(f"[COMPARISON] Top100% final: {original_top10_results['top']['portfolio_values'][-1]}")
        
        percent_results = rebalance_portfolio_percent(
            rdata,
            list(factor_objects),
            start_year=start_year_for_percent,
            end_year=2023,
            initial_aum=results.get('portfolio_values', [1])[0],
            n_percent=n_percent,
            include_bottom=include_bottom,
            restrict_fossil_fuels=restrict_fossil_fuels
        )

        # Defensive checks: ensure we have a dict and expected keys to avoid KeyError in Colab
        if not isinstance(percent_results, dict):
            raise RuntimeError("rebalance_portfolio_percent did not return a dict")

        # Ensure top/bottom structure exists and normalize portfolio_values to Python lists
        percent_results.setdefault('top', {})
        raw_top_vals = percent_results['top'].get('portfolio_values', []) or []
        if isinstance(raw_top_vals, (pd.Series, np.ndarray)):
            top_vals = list(raw_top_vals)
        elif isinstance(raw_top_vals, str):
            try:
                top_vals = list(ast.literal_eval(raw_top_vals))
            except Exception:
                top_vals = [raw_top_vals]
        else:
            # safe-cast iterables (tuple, etc.) to list; handle None
            try:
                top_vals = list(raw_top_vals) if raw_top_vals is not None else []
            except Exception:
                top_vals = [raw_top_vals]
        percent_results['top']['portfolio_values'] = top_vals

        percent_results.setdefault('bottom', {})
        raw_bottom_vals = percent_results['bottom'].get('portfolio_values', None)
        if raw_bottom_vals is None:
            bottom_vals = None
        elif isinstance(raw_bottom_vals, (pd.Series, np.ndarray)):
            bottom_vals = list(raw_bottom_vals)
        elif isinstance(raw_bottom_vals, str):
            try:
                bottom_vals = list(ast.literal_eval(raw_bottom_vals))
            except Exception:
                bottom_vals = [raw_bottom_vals]
        else:
            try:
                bottom_vals = list(raw_bottom_vals)
            except Exception:
                bottom_vals = [raw_bottom_vals]
        percent_results['bottom']['portfolio_values'] = bottom_vals

        # Ensure years: if missing or falsy, derive from top values; otherwise keep as provided
        if not percent_results.get('years'):
            if top_vals:
                percent_results['years'] = list(range(start_year_for_percent, start_year_for_percent + len(top_vals)))
            else:
                percent_results['years'] = []

        # Ensure benchmark_returns exists (may be used by plotting); default to empty list
        percent_results.setdefault('benchmark_returns', [])

        # Determine a safe initial investment value for plotting
        initial_aum = percent_results.get('initial_aum')
        if initial_aum is None:
            if top_vals:
                initial_aum = top_vals[0]
            else:
                initial_aum = results.get('portfolio_values', [1])[0]

        # Call the visualization with the same style as plot_portfolio_growth (named args)
        plot_top_index_bottom(
            years=percent_results.get('years', []),
            top_values=percent_results['top'].get('portfolio_values', []),
            bottom_values=percent_results['bottom'].get('portfolio_values', None),
            portfolio_values=results.get('portfolio_values'),
            selected_factors=list(factor_names),
            restrict_fossil_fuels=restrict_fossil_fuels,
            benchmark_returns=percent_results.get('benchmark_returns', []),
            top_label=f"Top {n_percent}%",
            bottom_label=f"Bottom {n_percent}%",
            initial_investment=initial_aum
        )


if __name__ == "__main__":
    main()

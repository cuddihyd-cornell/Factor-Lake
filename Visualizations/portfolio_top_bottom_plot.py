import matplotlib.pyplot as plt
import numpy as np
from calculate_holdings import get_benchmark_return  # ensure same source/units as other plot

def plot_top_index_bottom(years,
                          top_values,
                          bottom_values=None,
                          portfolio_values=None,
                          selected_factors=None,
                          restrict_fossil_fuels=False,
                          benchmark_returns=None,
                          top_label='Top n%',
                          index_label='Benchmark',
                          bottom_label='Bottom n%',
                          initial_investment=None,
                          top_color='tab:green',
                          index_color='tab:blue',
                          bottom_color='tab:red',
                          portfolio_color='k',
                          show=True,
                          figsize=(10,6)):
    """
    Plot Portfolio, Top n% -> Benchmark -> Bottom n% on the same axes.

    Parameters mirror the style used by plot_portfolio_growth in main.py:
      - years: list of years (len = T+1)
      - top_values: list of portfolio AUM values for top n% (len = T+1)
      - bottom_values: optional list of portfolio AUM values for bottom n% (len = T+1)
      - selected_factors, restrict_fossil_fuels: passed for consistency (not used in plotting)
      - benchmark_returns: list/array of benchmark returns as decimals (len = T)
      - initial_investment: initial AUM (used if benchmark_returns provided to build cumulative series)
    """
    years = list(years)
    top_vals = list(top_values)
    bottom_vals = list(bottom_values) if bottom_values is not None else None
    portfolio_vals = list(portfolio_values) if portfolio_values is not None else None

    # determine initial value used to start benchmark
    initial = initial_investment if initial_investment is not None else (portfolio_vals[0] if portfolio_vals else (top_vals[0] if top_vals else 1.0))

    # Build benchmark cumulative series using same source as portfolio_growth_plot
    benchmark_cum = None
    if benchmark_returns is None:
        # compute from get_benchmark_return for each year in years[:-1]
        benchmark_cum = [initial]
        for year in years[:-1]:
            r_pct = get_benchmark_return(year)  # returns percent (e.g., 34.62)
            r = r_pct / 100.0
            benchmark_cum.append(benchmark_cum[-1] * (1 + r))
    else:
        # Accept either percent (e.g., [34.62,...]) or decimals ([0.3462,...])
        br = np.array(benchmark_returns, dtype=float)
        if np.nanmax(np.abs(br)) > 2:  # likely given in percent
            br = br / 100.0
        # Ensure length aligns: expect len(br) == len(years)-1; if longer/short, iterate min length
        benchmark_cum = [initial]
        for r in br[:max(0, len(years)-1)]:
            benchmark_cum.append(benchmark_cum[-1] * (1 + r))
        # if br shorter, pad with last value repeated to match years length
        while len(benchmark_cum) < len(years):
            benchmark_cum.append(benchmark_cum[-1])

    plt.figure(figsize=figsize)
    if portfolio_vals is not None:
        plt.plot(years, portfolio_vals, marker='o', color=portfolio_color, linewidth=2, label='Portfolio', zorder=5)
    plt.plot(years, top_vals, marker='o', color=top_color, label=top_label, zorder=4)
    if benchmark_cum is not None:
        plt.plot(years, benchmark_cum, marker='o', color=index_color, linestyle='--', label=index_label, zorder=3)
    if bottom_vals is not None:
        plt.plot(years, bottom_vals, marker='o', color=bottom_color, linestyle=':', label=bottom_label, zorder=2)

    plt.xlabel('Year')
    plt.ylabel('Portfolio Value')
    plt.title(f'{top_label} vs {index_label} vs {bottom_label}')
    plt.grid(True)
    plt.legend()
    if show:
        plt.show()
    else:
        return plt.gca()
import matplotlib.pyplot as plt
import numpy as np

def plot_top_index_bottom(years,
                          top_values,
                          bottom_values=None,
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
                          show=True,
                          figsize=(10,6)):
    """
    Plot Top n% -> Benchmark -> Bottom n% on the same axes.

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

    # Build benchmark cumulative series
    if benchmark_returns is None:
        benchmark_cum = None
    else:
        initial = initial_investment if initial_investment is not None else (top_vals[0] if top_vals else 1.0)
        benchmark_cum = [initial]
        for r in benchmark_returns:
            benchmark_cum.append(benchmark_cum[-1] * (1 + r))

    plt.figure(figsize=figsize)
    plt.plot(years, top_vals, marker='o', color=top_color, label=top_label)
    if benchmark_cum is not None:
        plt.plot(years, benchmark_cum, marker='o', color=index_color, linestyle='--', label=index_label)
    if bottom_vals is not None:
        plt.plot(years, bottom_vals, marker='o', color=bottom_color, linestyle=':', label=bottom_label)

    plt.xlabel('Year')
    plt.ylabel('Portfolio Value')
    plt.title(f'{top_label} vs {index_label} vs {bottom_label}')
    plt.grid(True)
    plt.legend()
    if show:
        plt.show()
    else:
        return plt.gca()
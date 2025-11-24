import matplotlib.pyplot as plt
import numpy as np

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
    Accepts benchmark_returns either as decimals (0.12) or percentages (12.0) and normalizes.
    """
    years = list(years)
    top_vals = list(top_values)
    bottom_vals = list(bottom_values) if bottom_values is not None else None
    portfolio_vals = list(portfolio_values) if portfolio_values is not None else None

    # Normalize benchmark_returns: if values look like percents (> 1.5), convert to decimals
    benchmark_cum = None
    if benchmark_returns is not None:
        br_arr = np.array(benchmark_returns, dtype=float)
        if br_arr.size > 0 and np.nanmax(np.abs(br_arr)) > 1.5:
            br_arr = br_arr / 100.0
        initial = initial_investment if initial_investment is not None else (portfolio_vals[0] if portfolio_vals else (top_vals[0] if top_vals else 1.0))
        benchmark_cum = [initial]
        for r in br_arr:
            benchmark_cum.append(benchmark_cum[-1] * (1 + r))

    plt.figure(figsize=figsize)
    # Plot order: portfolio (baseline), top (expected highest), benchmark (index), bottom (expected lowest)
    if portfolio_vals is not None:
        plt.plot(years, portfolio_vals, marker='o', color=portfolio_color, linewidth=2, label='Portfolio', zorder=4)
    plt.plot(years, top_vals, marker='o', color=top_color, label=top_label, zorder=3)
    if benchmark_cum is not None:
        plt.plot(years, benchmark_cum, marker='o', color=index_color, linestyle='--', label=index_label, zorder=2)
    if bottom_vals is not None:
        plt.plot(years, bottom_vals, marker='o', color=bottom_color, linestyle=':', label=bottom_label, zorder=1)

    plt.xlabel('Year')
    plt.ylabel('Portfolio Value')
    plt.title(f'{top_label} vs {index_label} vs {bottom_label}')
    plt.grid(True)
    plt.legend()
    if show:
        plt.show()
    else:
        return plt.gca()
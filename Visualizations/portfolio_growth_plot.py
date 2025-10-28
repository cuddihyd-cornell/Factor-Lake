# portfolio_growth_plot.py

from matplotlib.pylab import double
import matplotlib.pyplot as plt


def plot_portfolio_growth(years,
                          portfolio_values,
                          selected_factors=None,
                          restrict_fossil_fuels=False,
                          benchmark_returns=None,
                          benchmark_label='Russell 2000',
                          initial_investment=None):
    """
    Plots the growth of a portfolio over time and optionally plots a benchmark
    (Russell 2000) dollar-invested series alongside it.

    Parameters:
        years (list[int]): List of years (e.g., [2002, 2003, ..., 2023])
        portfolio_values (list[float]): Portfolio values corresponding to each year
        selected_factors (list[str] | tuple[str] | None): Factor names used to build the portfolio
        restrict_fossil_fuels (bool): Whether fossil fuel companies were excluded
        benchmark_returns (list[float] | None): Year-by-year benchmark returns. Can be
            percentages (e.g. 34.62) or decimals (e.g. 0.3462). Expected length is
            either len(years)-1 (returns between successive years) or len(years).
        benchmark_label (str): Label to use for the benchmark in the legend.
        initial_investment (float | None): Starting dollar value for the benchmark
            series; if None, the function will use portfolio_values[0] when available
            or 1.0 as a fallback.
    """

    plt.figure(figsize=(10, 6))

    # Build a readable label from factor names if provided
    if selected_factors:
        factor_names = [str(f) for f in selected_factors]
        factor_set_name = ", ".join(factor_names)
    else:
        factor_set_name = "Selected Factors"

    restriction_text = "Yes" if restrict_fossil_fuels else "No"

    # Plot portfolio values
    plt.plot(years, portfolio_values, marker='o', linestyle='-', color='b', label='Portfolio')

    # Compute and plot benchmark dollar-invested series if returns are provided
    benchmark_values = None
    if benchmark_returns is not None:
        # Defensive copy
        br = list(benchmark_returns)

        # Determine initial investment for benchmark
        if initial_investment is None:
            if portfolio_values and len(portfolio_values) > 0:
                initial_investment = portfolio_values[0]
            else:
                initial_investment = 1.0

        # Normalize return units: support both percent (e.g. 34.62) and decimal (0.3462)
        def to_decimal(x):
            try:
                v = double(x)
            except Exception:
                return 0.0
            return v if abs(v) <= 1 else v / 100.0

        # Expected common case: benchmark_returns has length len(years)-1
        if len(br) == max(0, len(years) - 1):
            benchmark_values = [initial_investment]
            for r in br:
                r_dec = to_decimal(r)
                benchmark_values.append(benchmark_values[-1] * (1 + r_dec))
        elif len(br) == len(years):
            # If returns length equals years, treat the sequence as returns between years
            benchmark_values = [initial_investment]
            for r in br[:-1]:
                r_dec = to_decimal(r)
                benchmark_values.append(benchmark_values[-1] * (1 + r_dec))
        else:
            # Can't align lengths reliably; skip plotting benchmark
            benchmark_values = None

    if benchmark_values is not None:
        # Ensure x-axis matches benchmark_values length
        if len(benchmark_values) == len(years):
            plt.plot(years, benchmark_values, marker='s', linestyle='--', color='r', label=benchmark_label)
        else:
            # Try to align by trimming or expanding years
            common_len = min(len(years), len(benchmark_values))
            plt.plot(years[:common_len], benchmark_values[:common_len], marker='s', linestyle='--', color='r', label=benchmark_label)

    plt.title(f"Portfolio Growth Over Time ({factor_set_name})\nFossil fuel restriction: {restriction_text}")
    plt.xlabel('Year')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

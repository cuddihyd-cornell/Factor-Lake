import matplotlib.pyplot as plt
from market_object import MarketObject
import math


def plot_top_bottom_percent(rdata,
                            factor,
                            years,
                            percent=10,
                            show_bottom=True,
                            restrict_fossil_fuels=False,
                            benchmark_returns=None,
                            benchmark_label='Russell 2000',
                            initial_investment=None):
    """
    Plot dollar-invested growth for the top-N% and optionally bottom-N% portfolios
    constructed from `factor` each year, alongside a benchmark.

    Parameters:
        rdata (pd.DataFrame): Full market data (must contain 'Year')
        factor (Factors): A factor object with .get(ticker, market) method
        years (list[int]): Ordered list of years to simulate (e.g. [2002,2003,...])
        percent (int): Percent (1-100) used to select top/bottom N% (100 disables bottom)
        show_bottom (bool): Whether to compute and plot bottom-N% portfolio
        restrict_fossil_fuels (bool): If True, filter fossil industries before computing
        benchmark_returns (list[float] | None): Optional benchmark returns (percent or decimal)
        initial_investment (float | None): Starting dollars for the simulated portfolios.
            If None, defaults to 1.0.
    """

    # Validate percent
    percent = int(percent)
    if percent < 1:
        percent = 1
    if percent > 100:
        percent = 100

    # If percent == 100, bottom is not meaningful
    if percent == 100:
        show_bottom = False

    if initial_investment is None:
        initial_investment = 1.0

    # Helper to compute top/bottom tickers for a given MarketObject
    def select_percent_tickers(market, pct, which='top'):
        factor_values = {}
        for ticker in market.stocks.index:
            try:
                v = factor.get(ticker, market)
                if v is None:
                    continue
                # Accept numeric values only
                if isinstance(v, (int, float)):
                    factor_values[ticker] = float(v)
            except Exception:
                continue

        if not factor_values:
            return []

        sorted_items = sorted(factor_values.items(), key=lambda x: x[1], reverse=True)
        n = max(1, math.floor(len(sorted_items) * (pct / 100.0)))
        if which == 'top':
            return [t for t, _ in sorted_items[:n]]
        else:
            return [t for t, _ in sorted_items[-n:]]

    # Prepare arrays
    top_values = [initial_investment]
    bottom_values = [initial_investment] if show_bottom else None

    # Simulate year-to-year rebalanced portfolios
    for i in range(len(years) - 1):
        year = years[i]
        next_year = years[i + 1]

        market = MarketObject(rdata.loc[rdata['Year'] == year], year)
        next_market = MarketObject(rdata.loc[rdata['Year'] == next_year], next_year)

        # Top
        top_tickers = select_percent_tickers(market, percent, 'top')
        start_top = 0.0
        end_top = 0.0
        # Build equal-dollar positions at start using market prices
        if top_tickers:
            equal = top_values[-1] / len(top_tickers)
            for t in top_tickers:
                entry = market.get_price(t)
                if entry is None or entry <= 0:
                    continue
                shares = equal / entry
                start_top += shares * entry
                # Use next market price where available
                exit_price = next_market.get_price(t)
                if exit_price is None:
                    exit_price = entry
                end_top += shares * exit_price
        else:
            # No tickers selected -- carry forward value
            end_top = top_values[-1]

        top_values.append(end_top)

        # Bottom
        if show_bottom:
            bottom_tickers = select_percent_tickers(market, percent, 'bottom')
            start_bottom = 0.0
            end_bottom = 0.0
            if bottom_tickers:
                equal_b = bottom_values[-1] / len(bottom_tickers)
                for t in bottom_tickers:
                    entry = market.get_price(t)
                    if entry is None or entry <= 0:
                        continue
                    shares = equal_b / entry
                    start_bottom += shares * entry
                    exit_price = next_market.get_price(t)
                    if exit_price is None:
                        exit_price = entry
                    end_bottom += shares * exit_price
            else:
                end_bottom = bottom_values[-1]
            bottom_values.append(end_bottom)

    # Years alignment: top_values and bottom_values now have length len(years)
    # Compute benchmark dollar series if provided (same logic as portfolio_growth_plot)
    benchmark_values = None
    if benchmark_returns is not None:
        def to_decimal(x):
            try:
                v = float(x)
            except Exception:
                return 0.0
            return v if abs(v) <= 1 else v / 100.0

        br = list(benchmark_returns)
        if len(br) == max(0, len(years) - 1):
            benchmark_values = [initial_investment]
            for r in br:
                benchmark_values.append(benchmark_values[-1] * (1 + to_decimal(r)))
        elif len(br) == len(years):
            benchmark_values = [initial_investment]
            for r in br[:-1]:
                benchmark_values.append(benchmark_values[-1] * (1 + to_decimal(r)))

    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(years, top_values, marker='o', linestyle='-', color='g', label=f'Top {percent}%')
    if show_bottom and bottom_values is not None:
        plt.plot(years, bottom_values, marker='o', linestyle='-', color='m', label=f'Bottom {percent}%')
    if benchmark_values is not None and len(benchmark_values) == len(years):
        plt.plot(years, benchmark_values, marker='s', linestyle='--', color='r', label=benchmark_label)

    plt.title(f"Top/Bottom {percent}% Portfolios ({factor}) vs {benchmark_label}")
    plt.xlabel('Year')
    plt.ylabel('Dollar Invested ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

import matplotlib.pyplot as plt
from market_object import MarketObject
import math


def plot_top_bottom_percent(rdata,
                            factors,
                            years,
                            percent=10,
                            show_bottom=True,
                            restrict_fossil_fuels=False,
                            benchmark_returns=None,
                            benchmark_label='Russell 2000',
                            initial_investment=None,
                            debug=False,
                            debug_years=3):
    """
    Plot dollar-invested growth for the top-N% and optionally bottom-N% portfolios
    constructed from `factor` each year, alongside a benchmark.

    Parameters:
        rdata (pd.DataFrame): Full market data (must contain 'Year')
        factors (list[Factors]): List of factor objects with .get(ticker, market)
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
        # Build per-factor rank dictionaries (rank normalized 0..1, higher is better)
        rank_dicts = []
        for factor in factors:
            values = {}
            for ticker in market.stocks.index:
                try:
                    v = factor.get(ticker, market)
                    if v is None:
                        continue
                    if isinstance(v, (int, float)):
                        values[ticker] = float(v)
                except Exception:
                    continue
            if not values:
                continue
            # compute ranks 0..1 ascending -> lower value rank 0, highest rank 1
            items = sorted(values.items(), key=lambda x: x[1])
            n_items = len(items)
            ranks = {}
            for idx, (t, _) in enumerate(items):
                ranks[t] = idx / (n_items - 1) if n_items > 1 else 0.5
            rank_dicts.append(ranks)

        if not rank_dicts:
            return []

        # combine ranks by averaging across available factor ranks per ticker
        combined = {}
        tickers_union = set().union(*[set(d.keys()) for d in rank_dicts])
        for t in tickers_union:
            vals = [d[t] for d in rank_dicts if t in d]
            if not vals:
                continue
            combined[t] = sum(vals) / len(vals)

        sorted_items = sorted(combined.items(), key=lambda x: x[1], reverse=True)
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

        # Debug printing for first few years to diagnose performance drivers
        if debug and i < debug_years:
            def avg_entry_and_returns(tickers):
                entries = []
                rets = []
                for t in tickers:
                    try:
                        entry = market.get_price(t)
                        exitp = next_market.get_price(t)
                        if entry is None:
                            continue
                        if exitp is None:
                            exitp = entry
                        entries.append(entry)
                        rets.append((exitp / entry) - 1 if entry else 0)
                    except Exception:
                        continue
                return (sum(entries) / len(entries)) if entries else None, (sum(rets) / len(rets)) if rets else None

            def avg_factor_values(tickers):
                vals = {}
                for f in factors:
                    vlist = []
                    for t in tickers:
                        try:
                            v = f.get(t, market)
                            if v is not None:
                                vlist.append(float(v))
                        except Exception:
                            continue
                    vals[str(f)] = (sum(vlist) / len(vlist)) if vlist else None
                return vals

            print(f"\nDEBUG Year {year} -> {next_year}")
            print(f" Top {percent}% tickers ({len(top_tickers)}): {top_tickers[:10]}{('...' if len(top_tickers)>10 else '')}")
            avg_entry_top, avg_ret_top = avg_entry_and_returns(top_tickers)
            print(f"  Top avg entry price: {avg_entry_top}, avg next-year return: {avg_ret_top}")
            print(f"  Top avg factor values: {avg_factor_values(top_tickers)}")

            if show_bottom:
                print(f" Bottom {percent}% tickers ({len(bottom_tickers)}): {bottom_tickers[:10]}{('...' if len(bottom_tickers)>10 else '')}")
                avg_entry_bot, avg_ret_bot = avg_entry_and_returns(bottom_tickers)
                print(f"  Bottom avg entry price: {avg_entry_bot}, avg next-year return: {avg_ret_bot}")
                print(f"  Bottom avg factor values: {avg_factor_values(bottom_tickers)}")

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

    # Build a readable factor-set name
    try:
        factor_set_name = ", ".join([str(f) for f in factors])
    except Exception:
        factor_set_name = "Selected Factors"

    plt.title(f"Top/Bottom {percent}% Portfolios ({factor_set_name}) vs {benchmark_label}")
    plt.xlabel('Year')
    plt.ylabel('Dollar Invested ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

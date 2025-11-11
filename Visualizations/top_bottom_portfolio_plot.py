import matplotlib.pyplot as plt
from market_object import MarketObject
import math

# Respect per-factor direction (higher_is_better) from the docs
from factors_doc import FACTOR_DOCS


def plot_top_bottom_percent(rdata,
                            factors,
                            years,
                            percent=10,
                            show_bottom=True,
                            restrict_fossil_fuels=False,
                            benchmark_returns=None,
                            benchmark_label='Russell 2000',
                            initial_investment=None,
                            require_all_factors=True,
                            verbose=False,
                            drop_missing_next_price=True):
    """
    Plot dollar-invested growth for the top-N% and optionally bottom-N% portfolios
    constructed from a list of factors each year, alongside a benchmark.

    Notes:
      - Ranks are normalized per-factor to [0..1] where 1 is most attractive. The
        factor direction is read from `factors_doc.FACTOR_DOCS` via the factor's
        `column_name` attribute (`higher_is_better`). If a factor has
        `higher_is_better == False` it will be inverted so lower raw values are
        treated as more attractive.
      - `drop_missing_next_price` controls whether tickers missing next-year
        prices are excluded from realized returns (recommended for clean tests).
    """

    percent = int(percent)
    if percent < 1:
        percent = 1
    if percent > 100:
        percent = 100

    if percent == 100:
        show_bottom = False

    if initial_investment is None:
        initial_investment = 1.0

    def select_percent_tickers(market, pct, which='top'):
        rank_dicts = []
        for factor in factors:
            values = {}
            col = getattr(factor, 'column_name', str(factor))
            for ticker in market.stocks.index:
                try:
                    v = factor.get(ticker, market)
                except Exception:
                    v = None
                if v is None:
                    continue
                try:
                    values[ticker] = float(v)
                except Exception:
                    continue
            if not values:
                continue

            higher_is_better = FACTOR_DOCS.get(col, {}).get('higher_is_better', True)
            items = sorted(values.items(), key=lambda x: x[1])  # low -> high
            n_items = len(items)
            ranks = {}
            if n_items == 1:
                ranks[items[0][0]] = 0.5
            else:
                for idx, (t, _) in enumerate(items):
                    base_rank = idx / (n_items - 1)
                    ranks[t] = base_rank if higher_is_better else (1.0 - base_rank)
            rank_dicts.append(ranks)

        if not rank_dicts:
            return [], 0, 0

        if require_all_factors:
            tickers_set = set(rank_dicts[0].keys())
            for d in rank_dicts[1:]:
                tickers_set &= set(d.keys())
            if not tickers_set:
                tickers_set = set().union(*[set(d.keys()) for d in rank_dicts])
        else:
            tickers_set = set().union(*[set(d.keys()) for d in rank_dicts])

        combined = {}
        for t in tickers_set:
            vals = [d[t] for d in rank_dicts if t in d]
            if not vals:
                continue
            combined[t] = sum(vals) / len(vals)

        sorted_items = sorted(combined.items(), key=lambda x: x[1], reverse=True)  # best->worst
        universe_size = len(sorted_items)
        n = max(1, math.floor(universe_size * (pct / 100.0)))
        if which == 'top':
            return [t for t, _ in sorted_items[:n]], universe_size, n
        else:
            return [t for t, _ in sorted_items[-n:]], universe_size, n

    top_values = [initial_investment]
    bottom_values = [initial_investment] if show_bottom else None

    for i in range(len(years) - 1):
        year = years[i]
        next_year = years[i + 1]

        market = MarketObject(rdata.loc[rdata['Year'] == year], year)
        next_market = MarketObject(rdata.loc[rdata['Year'] == next_year], next_year)

        # Top cohort
        top_tickers, universe_size_top, n_top = select_percent_tickers(market, percent, 'top')
        start_top = 0.0
        end_top = 0.0
        top_returns = []
        if top_tickers:
            equal = top_values[-1] / len(top_tickers)
            for t in top_tickers:
                entry = market.get_price(t)
                if entry is None or entry <= 0:
                    continue
                exit_price = next_market.get_price(t)
                if exit_price is None:
                    if drop_missing_next_price:
                        # skip this ticker entirely for realized return
                        continue
                    exit_price = entry
                shares = equal / entry
                start_top += shares * entry
                end_top += shares * exit_price
                try:
                    top_returns.append((exit_price / entry) - 1.0)
                except Exception:
                    top_returns.append(0.0)
        else:
            end_top = top_values[-1]

        top_values.append(end_top)

        # Bottom cohort
        universe_size_bot = None
        n_bot = 0
        bottom_tickers = []
        if show_bottom:
            assert bottom_values is not None
            bottom_tickers, universe_size_bot, n_bot = select_percent_tickers(market, percent, 'bottom')
            start_bottom = 0.0
            end_bottom = 0.0
            bottom_returns = []
            if bottom_tickers:
                equal_b = bottom_values[-1] / len(bottom_tickers)
                for t in bottom_tickers:
                    entry = market.get_price(t)
                    if entry is None or entry <= 0:
                        continue
                    exit_price = next_market.get_price(t)
                    if exit_price is None:
                        if drop_missing_next_price:
                            continue
                        exit_price = entry
                    shares = equal_b / entry
                    start_bottom += shares * entry
                    end_bottom += shares * exit_price
                    try:
                        bottom_returns.append((exit_price / entry) - 1.0)
                    except Exception:
                        bottom_returns.append(0.0)
            else:
                end_bottom = bottom_values[-1]
            bottom_values.append(end_bottom)

        # Verbose diagnostics if requested
        if verbose:
            print(f"Year {year}: universe_size={universe_size_top}, top_n={n_top}")
            if show_bottom:
                print(f"Year {year}: universe_size={universe_size_bot}, bottom_n={n_bot}")
            if top_tickers:
                print("  Top sample:", top_tickers[:10])
                try:
                    avg_top_r = sum(top_returns) / len(top_returns) if top_returns else 0.0
                except Exception:
                    avg_top_r = 0.0
                print(f"  Top avg next-year return: {avg_top_r*100:.2f}% | start ${start_top:.2f} end ${end_top:.2f}")
            if show_bottom and bottom_tickers:
                print("  Bottom sample:", bottom_tickers[:10])
                try:
                    avg_bot_r = sum(bottom_returns) / len(bottom_returns) if bottom_returns else 0.0
                except Exception:
                    avg_bot_r = 0.0
                print(f"  Bottom avg next-year return: {avg_bot_r*100:.2f}% | start ${start_bottom:.2f} end ${end_bottom:.2f}")

    # Build benchmark dollar series (same approach as other plotting code)
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

    # Plot
    plt.figure(figsize=(10, 6))
    plt.plot(years, top_values, marker='o', linestyle='-', color='g', label=f'Top {percent}%')
    if show_bottom and bottom_values is not None:
        plt.plot(years, bottom_values, marker='o', linestyle='-', color='m', label=f'Bottom {percent}%')
    if benchmark_values is not None and len(benchmark_values) == len(years):
        plt.plot(years, benchmark_values, marker='s', linestyle='--', color='r', label=benchmark_label)

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
    # end of function

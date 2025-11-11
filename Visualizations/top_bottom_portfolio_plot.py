import matplotlib.pyplot as plt
from market_object import MarketObject
import math
import pandas as pd

# reuse normalization used elsewhere to match selection logic
from factor_utils import normalize_series

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
                            drop_missing_next_price=False,
                            selection_mode='by_factor'):
    """
    Plot dollar-invested growth for the top-N% and optionally bottom-N% portfolios
    constructed from a list of factors each year, alongside a benchmark.

        Notes:
            - Ranks are normalized per-factor to [0..1] where 1 is most attractive.
                The factor direction is read from `factors_doc.FACTOR_DOCS` via the
                factor's `column_name` attribute (`higher_is_better`). If a factor has
                `higher_is_better == False` it will be inverted so lower raw values are
                treated as more attractive.
            - Defaults are chosen to be deterministic and robust: `selection_mode`
                defaults to 'by_factor' (this mirrors `calculate_holdings`' equal-
                allocation-across-factors behavior) and `drop_missing_next_price`
                defaults to True to avoid zero-return substitution bias caused by
                carrying forward entry prices for missing exits.
            - When `drop_missing_next_price=True` tickers without a next-year price
                are excluded from that year's realized returns. The allocation logic
                below will reallocate the factor's dollars equally among the remaining
                valid tickers so the portfolio is always fully invested (subject to
                available valid tickers).
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

    # thresholds for helpful runtime warnings (small cohorts)
    MIN_COHORT_WARNING = 3

    def select_percent_tickers(market, pct, which='top'):
        rank_dicts = []
        for factor in factors:
            # Build a per-ticker averaged value (treat nulls as zero when averaging)
            values = {}
            col = getattr(factor, 'column_name', str(factor))
            # If the factor has a column in the market, aggregate samples per ticker
            # Ignore null samples when averaging (do not treat them as zeros)
            if col in market.stocks.columns:
                series = pd.to_numeric(market.stocks[col], errors='coerce')
                # group by ticker index and average across non-null samples
                grouped = series.groupby(series.index).mean()
                grouped = grouped.dropna()
                for t, v in grouped.items():
                    try:
                        values[t] = float(v)
                    except Exception:
                        # skip non-convertible values
                        continue
            else:
                # Fall back to calling the factor getter per row, aggregate per ticker
                samples = {}
                for idx in market.stocks.index:
                    try:
                        v = factor.get(idx, market)
                    except Exception:
                        v = None
                    if v is None:
                        # ignore null sample
                        continue
                    try:
                        sample_val = float(v)
                    except Exception:
                        continue
                    samples.setdefault(idx, []).append(sample_val)
                for t, vals in samples.items():
                    if vals:
                        values[t] = float(sum(vals) / len(vals))
            if not values:
                continue

            higher_is_better = FACTOR_DOCS.get(col, {}).get('higher_is_better', True)
            # stable sort: by value then ticker so results are deterministic
            items = sorted(values.items(), key=lambda x: (x[1], x[0]))  # low -> high
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

        # stable sort by score then ticker to make selection deterministic
        sorted_items = sorted(combined.items(), key=lambda x: (x[1], x[0]), reverse=True)  # best->worst
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

        # initialize per-year per-factor stats containers so verbose printing is safe
        top_factor_stats = []
        bottom_factor_stats = []

        # Top cohort
        start_top = 0.0
        end_top = 0.0
        top_returns = []
        top_dropped = 0
        # aggregate list for verbose printing (populated in both selection modes)
        top_tickers = []
        universe_size_top = 0
        n_top = 0
        if selection_mode == 'combined':
            top_tickers, universe_size_top, n_top = select_percent_tickers(market, percent, 'top')
            if top_tickers:
                # pre-filter valid tickers so the allocation is fully invested
                valid = []
                for t in top_tickers:
                    entry = market.get_price(t)
                    if entry is None or entry <= 0:
                        continue
                    exit_price = next_market.get_price(t)
                    if exit_price is None:
                        if drop_missing_next_price:
                            continue
                        exit_price = entry
                    valid.append((t, entry, exit_price))
                top_dropped += (len(top_tickers) - len(valid))
                if valid:
                    equal = top_values[-1] / len(valid)
                    for t, entry, exit_price in valid:
                        shares = equal / entry
                        start_top += shares * entry
                        end_top += shares * exit_price
                        try:
                            top_returns.append((exit_price / entry) - 1.0)
                        except Exception:
                            top_returns.append(0.0)
                else:
                    end_top = top_values[-1]
        elif selection_mode == 'by_factor':
            # Match calculate_holdings: equal allocation to each factor, then equal-dollar across that factor's top-N
            n_factors = max(1, len(factors))
            per_factor_alloc = top_values[-1] / n_factors
            universe_size_top = 0
            n_top = 0
            # per-factor diagnostics: list of (factor_col, selected_count, valid_count, dropped_count)
            top_factor_stats = []
            for factor in factors:
                col = getattr(factor, 'column_name', str(factor))
                # prefer vectorized series if available
                if col in market.stocks.columns:
                    # aggregate multiple samples per ticker by averaging non-null samples
                    series = pd.to_numeric(market.stocks[col], errors='coerce')
                    grouped = series.groupby(series.index).mean()
                    grouped = grouped.dropna()
                    higher_is_better = FACTOR_DOCS.get(col, {}).get('higher_is_better', True)
                    # Use raw averaged values but convert to a score where higher is better
                    # (score = v for higher_is_better True, score = -v for False).
                    items = []
                    for t, v in grouped.items():
                        try:
                            val = float(v)
                        except Exception:
                            continue
                        score = val if higher_is_better else -val
                        items.append((t, score))
                else:
                    items = []
                    for t in market.stocks.index:
                        try:
                            v = factor.get(t, market)
                        except Exception:
                            v = None
                        if v is None:
                            continue
                        try:
                            items.append((t, float(v)))
                        except Exception:
                            continue
                items = sorted(items, key=lambda x: x[1], reverse=True)
                universe_size_top += len(items)
                n = max(1, math.floor(len(items) * (percent / 100.0))) if items else 0
                n_top += n
                top_list = [t for t, _ in items[:n]]
                # keep an aggregated list for verbose diagnostics
                top_tickers.extend(top_list)
                # compute valid tickers for this factor (entry + possibly exit)
                valid = []
                if top_list:
                    # pre-filter valid tickers so per-factor allocation is fully invested
                    for t in top_list:
                        entry = market.get_price(t)
                        if entry is None or entry <= 0:
                            continue
                        exit_price = next_market.get_price(t)
                        if exit_price is None:
                            if drop_missing_next_price:
                                continue
                            exit_price = entry
                        valid.append((t, entry, exit_price))
                    dropped = len(top_list) - len(valid)
                    top_dropped += dropped
                    top_factor_stats.append((col, len(top_list), len(valid), dropped))
                    if valid:
                        equal = per_factor_alloc / len(valid)
                        for t, entry, exit_price in valid:
                            shares = equal / entry
                            start_top += shares * entry
                            end_top += shares * exit_price
                            try:
                                top_returns.append((exit_price / entry) - 1.0)
                            except Exception:
                                top_returns.append(0.0)
                else:
                    # record zero selection for this factor
                    top_factor_stats.append((col, 0, 0, 0))
            # fallback if nothing selected
            if end_top == 0:
                end_top = top_values[-1]
        else:
            raise ValueError(f"Unknown selection_mode: {selection_mode}")

        top_values.append(end_top)

        # Bottom cohort
        universe_size_bot = None
        n_bot = 0
        bottom_tickers = []
        bot_dropped = 0
        # initialize these so verbose diagnostics don't reference possibly-unbound names
        start_bottom = 0.0
        end_bottom = 0.0
        bottom_returns = []
        if show_bottom:
            assert bottom_values is not None
            if selection_mode == 'combined':
                bottom_tickers, universe_size_bot, n_bot = select_percent_tickers(market, percent, 'bottom')
                if bottom_tickers:
                    # pre-filter valid tickers so allocation is fully invested
                    valid = []
                    for t in bottom_tickers:
                        entry = market.get_price(t)
                        if entry is None or entry <= 0:
                            continue
                        exit_price = next_market.get_price(t)
                        if exit_price is None:
                            if drop_missing_next_price:
                                continue
                            exit_price = entry
                        valid.append((t, entry, exit_price))
                    bot_dropped += (len(bottom_tickers) - len(valid))
                    if valid:
                        equal_b = bottom_values[-1] / len(valid)
                        for t, entry, exit_price in valid:
                            shares = equal_b / entry
                            start_bottom += shares * entry
                            end_bottom += shares * exit_price
                            try:
                                bottom_returns.append((exit_price / entry) - 1.0)
                            except Exception:
                                bottom_returns.append(0.0)
                    else:
                        end_bottom = bottom_values[-1]
                else:
                    end_bottom = bottom_values[-1]
            elif selection_mode == 'by_factor':
                n_factors = max(1, len(factors))
                per_factor_alloc_b = bottom_values[-1] / n_factors
                universe_size_bot = 0
                n_bot = 0
                # per-factor diagnostics for bottom
                bottom_factor_stats = []
                for factor in factors:
                    col = getattr(factor, 'column_name', str(factor))
                    if col in market.stocks.columns:
                        # aggregate multiple samples per ticker by averaging non-null samples
                        series = pd.to_numeric(market.stocks[col], errors='coerce')
                        grouped = series.groupby(series.index).mean()
                        grouped = grouped.dropna()
                        higher_is_better = FACTOR_DOCS.get(col, {}).get('higher_is_better', True)
                        items = []
                        for t, v in grouped.items():
                            try:
                                val = float(v)
                            except Exception:
                                continue
                            score = val if higher_is_better else -val
                            items.append((t, score))
                    else:
                        items = []
                        for t in market.stocks.index:
                            try:
                                v = factor.get(t, market)
                            except Exception:
                                v = None
                            if v is None:
                                continue
                            try:
                                items.append((t, float(v)))
                            except Exception:
                                continue
                    # stable sort: worst->best with deterministic tie-breaker
                    items = sorted(items, key=lambda x: (x[1], x[0]))  # worst->best
                    universe_size_bot += len(items)
                    n = max(1, math.floor(len(items) * (percent / 100.0))) if items else 0
                    n_bot += n
                    bot_list = [t for t, _ in items[:n]]
                    # collect tickers for verbose diagnostics
                    bottom_tickers.extend(bot_list)
                    if bot_list:
                        # pre-filter valid tickers so per-factor allocation is fully invested
                        valid = []
                        for t in bot_list:
                            entry = market.get_price(t)
                            if entry is None or entry <= 0:
                                continue
                            exit_price = next_market.get_price(t)
                            if exit_price is None:
                                if drop_missing_next_price:
                                    continue
                                exit_price = entry
                            valid.append((t, entry, exit_price))
                        dropped = len(bot_list) - len(valid)
                        bot_dropped += dropped
                        bottom_factor_stats.append((col, len(bot_list), len(valid), dropped))
                        if valid:
                            equal = per_factor_alloc_b / len(valid)
                            for t, entry, exit_price in valid:
                                shares = equal / entry
                                start_bottom += shares * entry
                                end_bottom += shares * exit_price
                                try:
                                    bottom_returns.append((exit_price / entry) - 1.0)
                                except Exception:
                                    bottom_returns.append(0.0)
                if end_bottom == 0:
                    end_bottom = bottom_values[-1]
            else:
                raise ValueError(f"Unknown selection_mode: {selection_mode}")
            bottom_values.append(end_bottom)

        # Verbose diagnostics if requested + some deterministic warnings (small cohorts / dropped tickers)
        if verbose:
            print(f"Year {year}: universe_size={universe_size_top}, top_n={n_top}")
        else:
            # still print small-cohort warnings even when not verbose
            pass

        if show_bottom and verbose:
            print(f"Year {year}: universe_size={universe_size_bot}, bottom_n={n_bot}")

        if top_tickers:
            if verbose:
                print("  Top sample:", top_tickers[:10])
            # per-factor stats if available
            try:
                if verbose and 'top_factor_stats' in locals() and top_factor_stats:
                    print("  Top per-factor (factor, selected, valid, dropped):")
                    for fcol, sel, valid_c, dropped in top_factor_stats:
                        print(f"    {fcol}: selected={sel}, valid={valid_c}, dropped={dropped}")
            except Exception:
                pass
            try:
                avg_top_r = sum(top_returns) / len(top_returns) if top_returns else 0.0
            except Exception:
                avg_top_r = 0.0
            print(f"  Top avg next-year return: {avg_top_r*100:.2f}% | start ${start_top:.2f} end ${end_top:.2f}")
            # report how many tickers were dropped due to missing prices (helpful diagnostic)
            if top_dropped:
                print(f"  Top dropped tickers this year (missing prices): {top_dropped}")
            if n_top and n_top < MIN_COHORT_WARNING:
                print(f"  Warning: Top cohort size is small ({n_top}); results will be noisy.")

        if show_bottom and bottom_tickers:
            if verbose:
                print("  Bottom sample:", bottom_tickers[:10])
            # per-factor stats for bottom if available
            try:
                if verbose and 'bottom_factor_stats' in locals() and bottom_factor_stats:
                    print("  Bottom per-factor (factor, selected, valid, dropped):")
                    for fcol, sel, valid_c, dropped in bottom_factor_stats:
                        print(f"    {fcol}: selected={sel}, valid={valid_c}, dropped={dropped}")
            except Exception:
                pass
            try:
                avg_bot_r = sum(bottom_returns) / len(bottom_returns) if bottom_returns else 0.0
            except Exception:
                avg_bot_r = 0.0
            print(f"  Bottom avg next-year return: {avg_bot_r*100:.2f}% | start ${start_bottom:.2f} end ${end_bottom:.2f}")
            if bot_dropped:
                print(f"  Bottom dropped tickers this year (missing prices): {bot_dropped}")
            if n_bot and n_bot < MIN_COHORT_WARNING:
                print(f"  Warning: Bottom cohort size is small ({n_bot}); results will be noisy.")

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

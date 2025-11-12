import matplotlib.pyplot as plt
from market_object import MarketObject
import math
import pandas as pd

# reuse normalization used elsewhere to match selection logic
from factor_utils import normalize_series

# Respect per-factor direction (higher_is_better) from the docs
from factors_doc import FACTOR_DOCS

# Optionally compute baseline portfolio values using calculate_holdings.rebalance_portfolio
try:
    from calculate_holdings import rebalance_portfolio
except Exception:
    rebalance_portfolio = None


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
                            verbose=True,
                            drop_missing_next_price=True,
                            selection_mode='by_factor',
                            return_details=False,
                            weight_mode='equal',
                            show_percent_guides=True,
                            baseline_portfolio_values=None,
                            baseline_pct=10,
                            use_rebalance_for_selection=False):
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

    def compute_raw_combined_scores(market):
        """Compute a combined raw score per ticker by averaging per-factor raw values.

        For each factor we compute a per-ticker mean across non-null samples (as
        implemented above). For factors where lower_is_better is True we flip the
        sign so that higher score always means more attractive. The function
        returns a list of tuples (ticker, score) sorted descending by score.
        """
        per_factor_values = []
        for factor in factors:
            col = getattr(factor, 'column_name', str(factor))
            values = {}
            if col in market.stocks.columns:
                series = pd.to_numeric(market.stocks[col], errors='coerce')
                grouped = series.groupby(series.index).mean().dropna()
                for t, v in grouped.items():
                    try:
                        values[t] = float(v)
                    except Exception:
                        continue
            else:
                samples = {}
                for idx in market.stocks.index:
                    try:
                        v = factor.get(idx, market)
                    except Exception:
                        v = None
                    if v is None:
                        continue
                    try:
                        sample_val = float(v)
                    except Exception:
                        continue
                    samples.setdefault(idx, []).append(sample_val)
                for t, vals in samples.items():
                    if vals:
                        values[t] = float(sum(vals) / len(vals))

            # convert raw values into a per-factor score where higher is better
            higher_is_better = FACTOR_DOCS.get(col, {}).get('higher_is_better', True)
            factor_scores = {t: (val if higher_is_better else -val) for t, val in values.items()}
            per_factor_values.append(factor_scores)

        # build universe and average across available factor scores per ticker
        if not per_factor_values:
            return []
        tickers_set = set().union(*[set(d.keys()) for d in per_factor_values])
        combined = {}
        for t in tickers_set:
            vals = [d[t] for d in per_factor_values if t in d]
            if not vals:
                continue
            combined[t] = sum(vals) / len(vals)

        # stable sort by score then ticker
        sorted_items = sorted(combined.items(), key=lambda x: (x[1], x[0]), reverse=True)
        return sorted_items

    top_values = [initial_investment]
    bottom_values = [initial_investment] if show_bottom else None

    # Detailed diagnostics collected per-year when requested. Structure:
    # { 'years': [..], 'per_year': [ { year, combined_scores, top: {positions, avg_return,start,end}, bottom: {...} } ] }
    details = {'years': [], 'per_year': []} if return_details else None

    # Optionally compute top/bottom series using the full rebalance backtest logic
    skip_inline_selection = False
    if use_rebalance_for_selection and rebalance_portfolio is not None:
        try:
            start_year = years[0]
            end_year = years[-1]
            # Top series using rebalance logic with user-selected percent
            res_top = rebalance_portfolio(rdata, factors, start_year, end_year, initial_investment, verbosity=0, restrict_fossil_fuels=restrict_fossil_fuels, top_pct=percent, which='top')
            top_values = res_top.get('portfolio_values', [initial_investment])
            # Bottom series using rebalance logic with user-selected percent
            if show_bottom:
                res_bot = rebalance_portfolio(rdata, factors, start_year, end_year, initial_investment, verbosity=0, restrict_fossil_fuels=restrict_fossil_fuels, top_pct=percent, which='bottom')
                bottom_values = res_bot.get('portfolio_values', [initial_investment])
            skip_inline_selection = True
        except Exception:
            # fallback to inline selection logic below
            skip_inline_selection = False

    # initialize variables used by both inline and rebalance-driven selection paths
    sorted_combined_scores = []
    top_positions = []
    bottom_positions = []
    start_top = end_top = start_bottom = end_bottom = 0.0
    top_returns = []
    bottom_returns = []
    top_dropped = bot_dropped = 0
    top_tickers = []
    bottom_tickers = []
    universe_size_top = None
    universe_size_bot = None
    n_top = 0
    n_bot = 0
    top_factor_stats = []
    bottom_factor_stats = []
    year = None

    if not skip_inline_selection:
        for i in range(len(years) - 1):
            year = years[i]
            next_year = years[i + 1]

            market = MarketObject(rdata.loc[rdata['Year'] == year], year)
            next_market = MarketObject(rdata.loc[rdata['Year'] == next_year], next_year)

            # initialize per-year per-factor stats containers so verbose printing is safe
            top_factor_stats = []
            bottom_factor_stats = []

            # Pre-compute combined raw scores for diagnostics / simple mode
            sorted_combined_scores = compute_raw_combined_scores(market)

            # Top cohort
            start_top = 0.0
            end_top = 0.0
            top_returns = []
            top_positions = []
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
                                r = (exit_price / entry) - 1.0
                            except Exception:
                                r = 0.0
                            top_returns.append(r)
                            top_positions.append({'ticker': t, 'entry': entry, 'exit': exit_price, 'shares': shares, 'weight': equal, 'return': r})
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
                                    r = (exit_price / entry) - 1.0
                                except Exception:
                                    r = 0.0
                                top_returns.append(r)
                                top_positions.append({'ticker': t, 'entry': entry, 'exit': exit_price, 'shares': shares, 'weight': equal, 'return': r})
                    else:
                        # record zero selection for this factor
                        top_factor_stats.append((col, 0, 0, 0))
                # fallback if nothing selected
                if end_top == 0:
                    end_top = top_values[-1]
            elif selection_mode == 'simple':
                # simple mode: compute per-ticker averaged scores across factors (signed)
                sorted_items = compute_raw_combined_scores(market)
                universe_size_top = len(sorted_items)
                n_top = max(1, math.floor(universe_size_top * (percent / 100.0))) if sorted_items else 0
                # verbose: show the full list of averages (truncated)
                if verbose:
                    print(f"  Combined per-ticker scores (top 50): {sorted_items[:50]}")
                top_tickers = [t for t, _ in sorted_items[:n_top]]
                if top_tickers:
                    # pre-filter valid tickers
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
                                r = (exit_price / entry) - 1.0
                            except Exception:
                                r = 0.0
                            top_returns.append(r)
                            top_positions.append({'ticker': t, 'entry': entry, 'exit': exit_price, 'shares': shares, 'weight': equal, 'return': r})
                    else:
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
            bottom_positions = []
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
                                    r = (exit_price / entry) - 1.0
                                except Exception:
                                    r = 0.0
                                bottom_returns.append(r)
                                bottom_positions.append({'ticker': t, 'entry': entry, 'exit': exit_price, 'shares': shares, 'weight': equal_b, 'return': r})
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
                                        r = (exit_price / entry) - 1.0
                                    except Exception:
                                        r = 0.0
                                    bottom_returns.append(r)
                                    bottom_positions.append({'ticker': t, 'entry': entry, 'exit': exit_price, 'shares': shares, 'weight': equal, 'return': r})
                    if end_bottom == 0:
                        end_bottom = bottom_values[-1]
                elif selection_mode == 'simple':
                    # simple mode for bottom: compute per-ticker averaged signed scores and pick bottom N%
                    sorted_items = compute_raw_combined_scores(market)
                    universe_size_bot = len(sorted_items)
                    n_bot = max(1, math.floor(universe_size_bot * (percent / 100.0))) if sorted_items else 0
                    if verbose:
                        print(f"  Combined per-ticker scores (bottom 50): {sorted_items[-50:]}")
                    # bottom picks are the lowest scores
                    bottom_tickers = [t for t, _ in sorted_items[-n_bot:]] if n_bot else []
                    if bottom_tickers:
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
                        dropped = len(bottom_tickers) - len(valid)
                        bot_dropped += dropped
                        if valid:
                            equal_b = bottom_values[-1] / len(valid)
                            for t, entry, exit_price in valid:
                                shares = equal_b / entry
                                start_bottom += shares * entry
                                end_bottom += shares * exit_price
                                try:
                                    r = (exit_price / entry) - 1.0
                                except Exception:
                                    r = 0.0
                                bottom_returns.append(r)
                                bottom_positions.append({'ticker': t, 'entry': entry, 'exit': exit_price, 'shares': shares, 'weight': equal_b, 'return': r})
                        else:
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
        # Collect structured details for this year if requested
        try:
            avg_top_r = sum(top_returns) / len(top_returns) if top_returns else 0.0
        except Exception:
            avg_top_r = 0.0
        try:
            avg_bot_r = sum(bottom_returns) / len(bottom_returns) if bottom_returns else 0.0
        except Exception:
            avg_bot_r = 0.0

        if details is not None:
            per_year = {
                'year': year,
                'combined_scores': sorted_combined_scores,
                'top': {
                    'positions': top_positions,
                    'avg_return': avg_top_r,
                    'start': start_top,
                    'end': end_top,
                    'dropped': top_dropped,
                    'n_selected': n_top,
                },
                'bottom': {
                    'positions': bottom_positions,
                    'avg_return': avg_bot_r,
                    'start': start_bottom,
                    'end': end_bottom,
                    'dropped': bot_dropped,
                    'n_selected': n_bot,
                }
            }
            details['years'].append(year)
            details['per_year'].append(per_year)

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
        # Plot bottom cohort normally so both series start at the same initial investment
        # and the bottom line will go down when the cohort loses value (e.g., < initial_investment).
        plt.plot(years, bottom_values, marker='o', linestyle='-', color='m', label=f'Bottom {percent}%')
    if benchmark_values is not None and len(benchmark_values) == len(years):
        plt.plot(years, benchmark_values, marker='s', linestyle='--', color='r', label=benchmark_label)

    # Optionally plot a baseline portfolio growth series (from portfolio_growth_plot)
    if baseline_portfolio_values is None and rebalance_portfolio is not None:
        try:
            # compute baseline portfolio values using the same factors and rdata
            start_year = years[0]
            end_year = years[-1]
            res = rebalance_portfolio(rdata, factors, start_year, end_year, initial_investment, verbosity=0, restrict_fossil_fuels=restrict_fossil_fuels, top_pct=baseline_pct)
            candidate = res.get('portfolio_values') if isinstance(res, dict) else None
            if candidate:
                baseline_portfolio_values = candidate
        except Exception:
            baseline_portfolio_values = None

    if baseline_portfolio_values is not None:
        try:
            bp = list(baseline_portfolio_values)
            if len(bp) == len(years):
                plt.plot(years, bp, marker='o', linestyle='-', color='b', label='Portfolio')
            else:
                common_len = min(len(years), len(bp))
                plt.plot(years[:common_len], bp[:common_len], marker='o', linestyle='-', color='b', label='Portfolio')
        except Exception:
            pass

    try:
        factor_set_name = ", ".join([str(f) for f in factors])
    except Exception:
        factor_set_name = "Selected Factors"

    plt.title(f"Top/Bottom {percent}% Portfolios ({factor_set_name}) vs {benchmark_label}")
    plt.xlabel('Year')
    plt.ylabel('Dollar Invested ($)')
    plt.grid(True)
    # show initial investment baseline for reference
    try:
        plt.axhline(initial_investment, color='k', linestyle=':', linewidth=0.8)
    except Exception:
        pass
    # Optionally draw horizontal guide lines at the cohorts' final percent returns (converted to dollars)
    # if show_percent_guides:
    #     try:
    #         # final values
    #         top_final = top_values[-1]
    #         top_pct = (top_final / initial_investment - 1.0) * 100.0
    #         plt.axhline(top_final, color='g', linestyle='--', linewidth=0.8)
    #         # annotate percentage on the right
    #         plt.text(years[-1], top_final, f"  {top_pct:+.1f}%", va='center', color='g')
    #     except Exception:
    #         pass
    #     if show_bottom and bottom_values is not None:
    #         try:
    #             bot_final = bottom_values[-1]
    #             bot_pct = (bot_final / initial_investment - 1.0) * 100.0
    #             plt.axhline(bot_final, color='m', linestyle='--', linewidth=0.8)
    #             plt.text(years[-1], bot_final, f"  {bot_pct:+.1f}%", va='center', color='m')
    #         except Exception:
    #             pass

    plt.legend()
    plt.tight_layout()
    plt.show()
    # end of function
    if details is not None:
        return details

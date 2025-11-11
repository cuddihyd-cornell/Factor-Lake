from market_object import MarketObject
from portfolio import Portfolio
import numpy as np
import pandas as pd
from factors_doc import FACTOR_DOCS
from factor_utils import normalize_series

def calculate_holdings(factor, aum, market, restrict_fossil_fuels=False):
    if restrict_fossil_fuels:
        industry_col = 'FactSet Industry'
        if industry_col in market.stocks.columns:
            fossil_keywords = ['oil', 'gas', 'coal', 'energy', 'fossil']
            series = market.stocks[industry_col].astype(str).str.lower()
            mask = series.apply(lambda x: not any(kw in x for kw in fossil_keywords) if pd.notna(x) else True)
            try:
                removed_tickers = list(market.stocks.loc[~mask].index)
                if removed_tickers:
                    print(f"Fossil filter (holdings) removed {len(removed_tickers)} tickers: {', '.join(removed_tickers[:25])}{' ...' if len(removed_tickers) > 25 else ''}")
            except Exception:
                pass
            market.stocks = market.stocks[mask].copy()

    factor_col = getattr(factor, 'column_name', str(factor))
    factor_values = {}

    if factor_col in market.stocks.columns:
        raw_series = pd.to_numeric(market.stocks[factor_col], errors='coerce')
        meta = FACTOR_DOCS.get(factor_col, {})
        higher_is_better = meta.get('higher_is_better', True)
        normed = normalize_series(raw_series, higher_is_better=higher_is_better)
        factor_values = normed.dropna().to_dict()
    else:
        factor_values = {
            ticker: factor.get(ticker, market)
            for ticker in market.stocks.index
            if isinstance(factor.get(ticker, market), (int, float))
        }

    if len(factor_values) == 0:
        return Portfolio(name=f"Portfolio_{market.t}")

    sorted_securities = sorted(factor_values.items(), key=lambda x: x[1], reverse=True)
    top_10_percent = sorted_securities[:max(1, len(sorted_securities) // 10)]

    portfolio_new = Portfolio(name=f"Portfolio_{market.t}")
    equal_investment = aum / len(top_10_percent)

    for ticker, _ in top_10_percent:
        price = market.get_price(ticker)
        if price is not None and price > 0:
            shares = equal_investment / price
            portfolio_new.add_investment(ticker, shares)

    return portfolio_new

def calculate_growth(portfolio, next_market, current_market, verbosity=0):
    total_start_value = sum(p.present_value(current_market) for p in portfolio)
    total_end_value = 0
    for p in portfolio:
        for inv in p.investments:
            ticker = inv["ticker"]
            end_price = next_market.get_price(ticker)
            if end_price is not None:
                total_end_value += inv["number_of_shares"] * end_price
            else:
                entry_price = current_market.get_price(ticker)
                if entry_price is not None:
                    total_end_value += inv["number_of_shares"] * entry_price
                    if verbosity == 3:
                        print(f"{ticker} - Missing in {next_market.t}, liquidating at entry price: {entry_price}")
    growth = (total_end_value - total_start_value) / total_start_value if total_start_value else 0
    return growth, total_start_value, total_end_value

def get_benchmark_return(year):
    benchmark_data = {
        2002: 34.62, 2003: 17.48, 2004: 16.56, 2005: 8.65, 2006: 11.01,
        2007: -15.63, 2008: -11.08, 2009: 11.89, 2010: -4.73, 2011: 30.01,
        2012: 28.22, 2013: 2.6, 2014: -0.09, 2015: 13.71, 2016: 19.11,
        2017: 13.8, 2018: -10.21, 2019: -1.03, 2020: 46.21, 2021: -24.48, 2022: 7.23
    }
    return benchmark_data.get(year, 0)

def calculate_information_ratio(portfolio_returns, benchmark_returns, verbosity=0):
    verbosity = 0 if verbosity is None else verbosity
    portfolio_returns = np.array(portfolio_returns)
    benchmark_returns = np.array(benchmark_returns)
    active_returns = portfolio_returns - benchmark_returns
    mean_active_return = np.mean(active_returns)
    tracking_error = np.std(active_returns, ddof=1)
    if tracking_error == 0:
        return None
    information_ratio = mean_active_return / tracking_error
    if verbosity >= 1:
        print(f"Information Ratio: {information_ratio:.4f}")
    return information_ratio

def rebalance_portfolio(data, factors, start_year, end_year, initial_aum, verbosity=None, restrict_fossil_fuels=False):
    aum = initial_aum
    years = [start_year]
    portfolio_returns = []
    benchmark_returns = []
    portfolio_values = [aum]
    
#Estimated Placeholders
    risk_free_rate_source = 'SOFR (Oct 1)'
    risk_free_rate_lookup = {
        2002: 0.015, 2003: 0.014, 2004: 0.017, 2005: 0.025, 2006: 0.035,
        2007: 0.045, 2008: 0.02, 2009: 0.005, 2010: 0.007, 2011: 0.01,
        2012: 0.012, 2013: 0.013, 2014: 0.015, 2015: 0.017, 2016: 0.018,
        2017: 0.02, 2018: 0.022, 2019: 0.018, 2020: 0.005, 2021: 0.01, 2022: 0.03
    }

    for year in range(start_year, end_year):
        market = MarketObject(data.loc[data['Year'] == year], year)
        yearly_portfolio = []

        for factor in factors:
            factor_portfolio = calculate_holdings(
                factor=factor,
                aum=aum / len(factors),
                market=market,
                restrict_fossil_fuels=restrict_fossil_fuels
            )
            yearly_portfolio.append(factor_portfolio)

        if year < end_year:
            next_market = MarketObject(data.loc[data['Year'] == year + 1], year + 1)
            growth, total_start_value, total_end_value = calculate_growth(yearly_portfolio, next_market, market, verbosity)

            if verbosity and verbosity >= 2:
                print(f"Year {year} to {year + 1}: Growth: {growth:.2%}, Start Value: ${total_start_value:.2f}, End Value: ${total_end_value:.2f}")

            aum = total_end_value
            portfolio_returns.append(growth)
            benchmark_return = get_benchmark_return(year) / 100
            benchmark_returns.append(benchmark_return)
            portfolio_values.append(aum)

        years.append(year + 1)

    if verbosity and verbosity >= 1:
        print("\n==== Final Summary ====")
        print(f"Initial Portfolio Value: ${initial_aum:.2f}")
        overall_growth = (aum - initial_aum) / initial_aum if initial_aum else 0
        print(f"Final Portfolio Value after {end_year}: ${aum:.2f}")
        print(f"Overall Growth from {start_year} to {end_year}: {overall_growth * 100:.2f}%")
        print(f"\n==== Performance Metrics ====")

    portfolio_np = np.array(portfolio_returns)
    benchmark_np = np.array(benchmark_returns)
    active_returns = portfolio_np - benchmark_np

    annualized_return_portfolio = (np.prod(1 + portfolio_np))**(1 / len(portfolio_np)) - 1
    annualized_return_benchmark = (np.prod(1 + benchmark_np))**(1 / len(benchmark_np)) - 1
    annualized_volatility_portfolio = np.std(portfolio_np, ddof=1)
    annualized_volatility_benchmark = np.std(benchmark_np, ddof=1)
    active_volatility = np.std(active_returns, ddof=1)

    print(f"Annualized Return (Portfolio): {annualized_return_portfolio:.2%}")
    print(f"Annualized Return (Benchmark): {annualized_return_benchmark:.2%}")
    print(f"Annualized Volatility (Portfolio): {annualized_volatility_portfolio:.2%}")
    print(f"Annualized Volatility (Benchmark): {annualized_volatility_benchmark:.2%}")
    print(f"Active Volatility (Portfolio vs Benchmark): {active_volatility:.2%}")

    information_ratio = calculate_information_ratio(portfolio_returns, benchmark_np, verbosity)
    if information_ratio is None:
        print("Information Ratio could not be calculated due to zero tracking error.")

    # === Advanced Stats ===
    rf_series = np.array([risk_free_rate_lookup.get(y, 0.01) for y in years[:-1]])
    excess_portfolio = portfolio_np - rf_series
    excess_benchmark = benchmark_np - rf_series

    peak_portfolio = np.maximum.accumulate(portfolio_values)
    drawdowns_portfolio = (np.array(portfolio_values) - peak_portfolio) / peak_portfolio
    max_drawdown_portfolio = drawdowns_portfolio.min()

    benchmark_cum = [initial_aum]
    for r in benchmark_np:
        benchmark_cum.append(benchmark_cum[-1] * (1 + r))
    peak_benchmark = np.maximum.accumulate(benchmark_cum)
    drawdowns_benchmark = (np.array(benchmark_cum) - peak_benchmark) / peak_benchmark
    max_drawdown_benchmark = drawdowns_benchmark.min()

    sharpe_portfolio = np.mean(excess_portfolio) / np.std(portfolio_np, ddof=1) if np.std(portfolio_np, ddof=1) else np.nan
    sharpe_benchmark = np.mean(excess_benchmark) / np.std(benchmark_np, ddof=1) if np.std(benchmark_np, ddof=1) else np.nan
    for i, (y, p, b) in enumerate(zip(years[1:], portfolio_np, benchmark_np)):
        print(f"{y}: Portfolio={p:.2%}, Benchmark={b:.2%}, Win={p > b}")
    win_rate = np.mean(portfolio_np > benchmark_np)

    if verbosity and verbosity >= 1:
        print("\n==== Advanced Backtest Stats ====")
        print(f"Risk-Free Rate Source: {risk_free_rate_source}")
        print(f"Max Drawdown (Portfolio): {max_drawdown_portfolio:.2%}")
        print(f"Max Drawdown (Benchmark): {max_drawdown_benchmark:.2%}")
        print(f"Sharpe Ratio (Portfolio): {sharpe_portfolio:.4f}")
        print(f"Sharpe Ratio (Benchmark): {sharpe_benchmark:.4f}")
        print(f"Yearly Win Rate vs Benchmark: {win_rate:.2%}")

    return {
        'final_value': aum,
        'yearly_returns': portfolio_returns,
        'benchmark_returns': [r * 100 for r in benchmark_np],
        'years': years,
        'portfolio_values': portfolio_values,
        'max_drawdown_portfolio': max_drawdown_portfolio,
        'max_drawdown_benchmark': max_drawdown_benchmark,
        'sharpe_portfolio': sharpe_portfolio,
        'sharpe_benchmark': sharpe_benchmark,
        'win_rate': win_rate,
        'risk_free_rate_source': risk_free_rate_source
    }

from market_object import MarketObject
from portfolio import Portfolio
import numpy as np
import pandas as pd

def calculate_holdings(factors, weights, aum, market, restrict_fossil_fuels=False):
    """
    Build a portfolio using weighted factors from Supabase data.
    Args:
        factors: list of factor objects (each with .column_name and .get())
        weights: list of floats, same length as factors
        aum: total assets under management
        market: MarketObject
        restrict_fossil_fuels: bool
    Returns:
        Portfolio object
    """
    if restrict_fossil_fuels:
        industry_col = 'FactSet Industry'
        if industry_col in market.stocks.columns:
            fossil_keywords = ['oil', 'gas', 'coal', 'energy', 'fossil']
            mask = market.stocks[industry_col].str.lower().apply(lambda x: not any(kw in x for kw in fossil_keywords) if pd.notna(x) else True)
            market.stocks = market.stocks[mask]

    # Use 'Ticker-Region' for tickers if present, else fallback to index
    if 'Ticker-Region' in market.stocks.columns:
        tickers = market.stocks['Ticker-Region']
    else:
        tickers = market.stocks.index

    factor_scores = {}
    for ticker in tickers:
        price = market.get_price(ticker)
        if price is None or pd.isna(price) or price <= 0:
            print(f"SKIP: {ticker} - Invalid price: {price}")
            continue
        values = []
        valid = True
        for factor in factors:
            value = factor.get(ticker, market)
            if value is None or pd.isna(value):
                print(f"SKIP: {ticker} - Missing value for factor '{factor.column_name}': {value}")
                valid = False
                break
            values.append(value)
        if not valid:
            continue
        # Weighted sum of factors
        score = sum(w * v for w, v in zip(weights, values))
        print(f"PASS: {ticker} - Price: {price}, Factor values: {values}, Score: {score}")
        factor_scores[ticker] = score

    if not factor_scores:
        print("WARNING: No valid securities after filtering. Returning empty Portfolio object.")
        return Portfolio(name=f"Portfolio_{market.t}")

    # Sort by weighted score
    sorted_securities = sorted(factor_scores.items(), key=lambda x: x[1], reverse=True)
    top_10_percent = sorted_securities[:max(1, len(sorted_securities) // 10)]

    portfolio_new = Portfolio(name=f"Portfolio_{market.t}")
    if len(top_10_percent) == 0:
        print("WARNING: No stocks passed the filtering criteria. Returning empty Portfolio object.")
        return portfolio_new

    equal_investment = aum / len(top_10_percent)
    for ticker, _ in top_10_percent:
        price = market.get_price(ticker)
        shares = equal_investment / price
        portfolio_new.add_investment(ticker, shares)

    return portfolio_new

def calculate_growth(portfolio, next_market, current_market, verbosity=0):
    # Calculate start value using the current market
    total_start_value = 0
    for factor_portfolio in portfolio:
        total_start_value += factor_portfolio.present_value(current_market)

    # Calculate end value using next market, handling missing stocks
    total_end_value = 0
    for factor_portfolio in portfolio:
        for inv in factor_portfolio.investments:
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

    # Calculate growth
    growth = (total_end_value - total_start_value) / total_start_value if total_start_value else 0
    return growth, total_start_value, total_end_value


def rebalance_portfolio(data, factors, start_year, end_year, initial_aum, verbosity=None, restrict_fossil_fuels=False):
    aum = initial_aum
    years = [start_year] # Start with the initial year
    portfolio_returns = []  # Store yearly returns for Information Ratio
    benchmark_returns = []  # Store benchmark returns for comparison
    portfolio_values = [aum]  # track total AUM over time

    # Use equal weights if not provided externally
    weights = [1.0] * len(factors)
    for year in range(start_year, end_year):
        market = MarketObject(data.loc[data['Year'] == year], year)
        # Build portfolio for this year using weighted factors
        factor_portfolio = calculate_holdings(
            factors=factors,
            weights=weights,
            aum=aum,
            market=market,
            restrict_fossil_fuels=restrict_fossil_fuels
        )
        yearly_portfolio = [factor_portfolio]

        if year < end_year:
            next_market = MarketObject(data.loc[data['Year'] == year + 1], year + 1)
            growth, total_start_value, total_end_value = calculate_growth(yearly_portfolio, next_market, market, verbosity)

            if verbosity is not None and verbosity >= 2:
                print(f"Year {year} to {year + 1}: Growth: {growth:.2%}, "
                      f"Start Value: ${total_start_value:.2f}, End Value: ${total_end_value:.2f}")

            aum = total_end_value  # Liquidate and reinvest
            portfolio_returns.append(growth)
            benchmark_return = get_benchmark_return(year)
            benchmark_returns.append(benchmark_return)
            portfolio_values.append(aum)

        years.append(year+1)

    
    if verbosity is not None and verbosity >= 1:

        print("\n==== Final Summary ====")
        print(f"Initial Portfolio Value: ${initial_aum:.2f}")
        # Calculate overall growth
        overall_growth = (aum - initial_aum) / initial_aum if initial_aum else 0
        print(f"Final Portfolio Value after {end_year}: ${aum:.2f}")
        print(f"Overall Growth from {start_year} to {end_year}: {overall_growth * 100:.2f}%")
  
    # Calculate Information Ratio
    information_ratio = calculate_information_ratio(portfolio_returns, benchmark_returns, verbosity)
    if information_ratio is None:
        print("Information Ratio could not be calculated due to zero tracking error.")
        
    return {
        'final_value': aum,
        'yearly_returns': portfolio_returns,
        'benchmark_returns': benchmark_returns,
        'years': years,
        'portfolio_values': portfolio_values
     }
    
def get_benchmark_return(year):
    """
    This function should return the benchmark return for the given year.
    """
    # Data from Factset (September)
    benchmark_data = {
        2002: 34.62, 2003: 17.48, 2004: 16.56, 2005: 8.65, 2006: 11.01,
        2007: -15.63, 2008: -11.08, 2009: 11.89, 2010: -4.73, 2011: 30.01,
        2012: 28.22, 2013: 2.6, 2014: -0.09, 2015: 13.71, 2016: 19.11,
        2017: 13.8, 2018: -10.21, 2019: -1.03, 2020: 46.21, 2021: -24.48, 2022: 7.23
    }
    return benchmark_data.get(year, 0)

def calculate_information_ratio(portfolio_returns, benchmark_returns, verbosity=0):
    """
    Calculates the Information Ratio (IR) for a given set of portfolio returns and benchmark returns.
    
    Parameters:
        portfolio_returns (list or np.array): List of portfolio returns over time.
        benchmark_returns (list or np.array): List of benchmark returns over time.
    
    Returns:
        float: The Information Ratio value.
    """
    # Ensure inputs are numpy arrays for mathematical operations
    verbosity = 0 if verbosity is None else verbosity
    portfolio_returns = np.array(portfolio_returns)
    benchmark_returns = np.array(benchmark_returns)

    # Calculate active returns
    active_returns = portfolio_returns - benchmark_returns
    
    # Calculate the mean active return (numerator)
    mean_active_return = np.mean(active_returns)
    
    # Calculate tracking error (denominator)
    tracking_error = np.std(active_returns, ddof=1)  # Use sample std deviation

    # Prevent division by zero
    if tracking_error == 0:
        return None  # Or return float('nan') to indicate undefined IR
    
    # Compute Information Ratio
    information_ratio = mean_active_return / tracking_error
    if verbosity >=1:
        print(f"Information Ratio: {information_ratio:.4f}")
    return information_ratio

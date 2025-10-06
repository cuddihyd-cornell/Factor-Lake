from market_object import load_data
from calculate_holdings import rebalance_portfolio
from user_input import get_factors
from verbosity_options import get_verbosity_level
from fossil_fuel_restriction import get_fossil_fuel_restriction
from portfolio_growth_plot import plot_portfolio_growth
import pandas as pd

def main():
    ### Load market data ###
    print("Loading market data...")
    rdata = load_data()
    
    ### Optional: Filter out fossil fuel-related industries ###
    restrict_fossil_fuels = get_fossil_fuel_restriction()
    
    ### Data preprocessing ###
    print("Processing market data...")
    rdata['Ticker'] = rdata['Ticker-Region'].dropna().apply(lambda x: x.split('-')[0].strip())
    rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year
    
    available_factors = [
        'ROE using 9/30 Data', 'ROA using 9/30 Data', '12-Mo Momentum %', '6-Mo Momentum %',
        '1-Mo Momentum %', 'Price to Book Using 9/30 Data', 'Next FY Earns/P', '1-Yr Price Vol %',
        'Accruals/Assets', 'ROA %', '1-Yr Asset Growth %', '1-Yr CapEX Growth %',
        'Book/Price', "Next-Year's Return %", "Next-Year's Active Return %"
    ]
    rdata = rdata[['Ticker', 'Ending Price', 'Year'] + available_factors]
    
    factors = get_factors(available_factors)
    verbosity_level = get_verbosity_level()

    ### Rebalancing portfolio across years ###
    print("\nRebalancing portfolio...")
    results = rebalance_portfolio(
        data=rdata,
        factors=factors,
        start_year=2002,
        end_year=2023,
        initial_aum=1,
        verbosity=verbosity_level,
        restrict_fossil_fuels=restrict_fossil_fuels
    )

    ### Plot portfolio growth ###
    print("\nPlotting portfolio growth...")
    plot_portfolio_growth(results['years'], results['portfolio_values'])

if __name__ == "__main__":
    main()

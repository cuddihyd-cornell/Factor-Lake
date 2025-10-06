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
    restrict_fossil_fuels = get_fossil_fuel_restriction()  # Prompt user for restriction
    if restrict_fossil_fuels:
        excluded_industries = [
            "Integrated Oil",
            "Oilfield Services/Equipment",
            "Oil & Gas Production"
        ]
        if 'FactSet Industry' in rdata.columns:
            original_len = len(rdata)
            rdata = rdata[~rdata['FactSet Industry'].isin(excluded_industries)].copy()
            print(f"Filtered out {original_len - len(rdata)} fossil fuel-related companies.")
            print(f"Fossil Fuel Keywords = ['oil', 'gas', 'coal', 'energy', 'fossil']")
        else:
            print("Warning: 'FactSet Industry' column not found. Cannot apply fossil fuel filter.")

    ### Data preprocessing ###
    print("Processing market data...")
    rdata['Ticker'] = rdata['Ticker-Region'].dropna().apply(lambda x: x.split('-')[0].strip())
    rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year
    available_factors = ['ROE using 9/30 Data', 'ROA using 9/30 Data', '12-Mo Momentum %', '6-Mo Momentum %', '1-Mo Momentum %', 'Price to Book Using 9/30 Data', 'Next FY Earns/P', '1-Yr Price Vol %', 'Accruals/Assets', 'ROA %', '1-Yr Asset Growth %', '1-Yr CapEX Growth %', 'Book/Price', 'Next-Year\'s Return %', 'Next-Year\'s Active Return %']
    rdata = rdata[['Ticker', 'Ending Price', 'Year'] + available_factors]
    factors = get_factors(available_factors)
    verbosity_level = get_verbosity_level() 

    ### Rebalancing portfolio across years ###
    print("\nRebalancing portfolio...")
    rebalance_portfolio(rdata, factors, start_year=2002, end_year=2023, initial_aum=1, verbosity=verbosity_level)

if __name__ == "__main__":
    main()

from market_object import load_data
from calculate_holdings import rebalance_portfolio
from user_input import get_factors
from verbosity_options import get_verbosity_level
from fossil_fuel_restriction import get_fossil_fuel_restriction
from Visualizations.portfolio_growth_plot import plot_portfolio_growth
import pandas as pd
import matplotlib.pyplot as plt

def main():
    ### Ask about fossil fuel restriction first ###
    restrict_fossil_fuels = get_fossil_fuel_restriction()  # Prompt user (Yes/No)

    # Ask user if they want to use Supabase or Excel
    use_supabase = False
    try:
        use_supabase_input = input("Load data from Supabase? (Yes/No): ").strip().lower()
        if use_supabase_input in ["yes", "y"]:
            use_supabase = True
    except Exception:
        pass

    ### Load market data (with or without restriction) ###
    print("Loading market data...")
    rdata = load_data(restrict_fossil_fuels=restrict_fossil_fuels, use_supabase=use_supabase)

    ### Optional: Filter out fossil fuel-related industries ###
    if restrict_fossil_fuels:
        fossil_fuel_keywords = [
            "coal",
            "oil",
            "gas",
            "petroleum",
            "fossil",
            "fuel",
            "mining",
            "drilling",
            "pipeline",
            "refining"
        ]
        def is_fossil_fuel_industry(industry_name):
            if not isinstance(industry_name, str):
                return False
            normalized = industry_name.lower().replace("&", "and").replace("/", " ")
            return any(keyword in normalized for keyword in fossil_fuel_keywords)
        if 'FactSet Industry' in rdata.columns:
            original_len = len(rdata)
            rdata = rdata[~rdata['FactSet Industry'].apply(is_fossil_fuel_industry)].copy()
            print(f"Filtered out {original_len - len(rdata)} companies with fossil fuel keywords in industry name.")
            print(f"Fossil Fuel Keywords = {fossil_fuel_keywords}")
        else:
            print("Warning: 'FactSet Industry' column not found. Cannot apply fossil fuel filter.")

    ### Data preprocessing ###
    print("Processing market data...")
    rdata['Ticker'] = rdata['Ticker-Region'].dropna().apply(lambda x: x.split('-')[0].strip())
    rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year

    available_factors = [
        'ROE using 9/30 Data', 'ROA using 9/30 Data', '12-Mo Momentum %',
        '6-Mo Momentum %', '1-Mo Momentum %', 'Price to Book Using 9/30 Data',
        'Next FY Earns/P', '1-Yr Price Vol %', 'Accruals/Assets', 'ROA %',
        '1-Yr Asset Growth %', '1-Yr CapEX Growth %', 'Book/Price',
        "Next-Year's Return %", "Next-Year's Active Return %"
    ]
    rdata = rdata[['Ticker', 'Ending Price', 'Year'] + available_factors]

    ### Get user selections ###
    factors = get_factors(available_factors)
    verbosity_level = get_verbosity_level()

    # Separate factor objects from their names for use downstream
    factor_objects, factor_names = (zip(*factors) if factors else ([], []))

    ### Rebalancing portfolio across years ###
    print("\nRebalancing portfolio...")
    results = rebalance_portfolio(
        rdata, list(factor_objects),
        start_year=2002, end_year=2023,
        initial_aum=1,
        verbosity=verbosity_level,
        restrict_fossil_fuels=restrict_fossil_fuels
    )
    
    # Plot portfolio growth
    plot_portfolio_growth(
        years=results['years'],
        portfolio_values=results['portfolio_values'],
        selected_factors=list(factor_names),
        restrict_fossil_fuels=restrict_fossil_fuels
    )


if __name__ == "__main__":
    main()

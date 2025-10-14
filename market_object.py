import pandas as pd
import numpy as np
from supabase_client import create_supabase_client
import os

### CREATING FUNCTION TO LOAD DATA ###
def load_data(restrict_fossil_fuels=False, use_supabase=True, table_name='FR2000 Annual Quant Data'):
    """
    Load market data from either Supabase or Excel file (fallback).
    
    Args:
        restrict_fossil_fuels (bool): Whether to exclude fossil fuel companies
        use_supabase (bool): If True, use Supabase; if False, use Excel fallback
        table_name (str): Name of Supabase table containing market data
    
    Returns:
        pandas.DataFrame: Market data
    """
    
    if use_supabase:
        try:
            # Create Supabase client
            client = create_supabase_client()
            
            # Load data from Supabase
            rdata = client.load_market_data(
                table_name=table_name,
                restrict_fossil_fuels=restrict_fossil_fuels
            )
            
            if rdata.empty:
                print("Warning: No data loaded from Supabase. Check your table and connection.")
                return rdata
            
            # Standardize column names to match existing code expectations
            rdata = _standardize_column_names(rdata)

            print(f"Successfully loaded {len(rdata)} records from Supabase")
            # Quick sanity check: distribution by Year after standardization
            if 'Year' in rdata.columns:
                try:
                    year_counts = rdata['Year'].value_counts().sort_index()
                    # Print a compact summary
                    print("Rows per Year (Supabase):", ", ".join([f"{int(y)}: {int(c)}" for y, c in year_counts.items()]))
                except Exception:
                    pass
            return rdata
            
        except Exception as e:
            print(f"Error loading from Supabase: {e}")
            print("Falling back to Excel file...")
            use_supabase = False
    
    if not use_supabase:
        # Fallback to Excel file (original implementation)
        file_path = '/content/drive/My Drive/Cayuga Fund Factor Lake/FR2000 Annual Quant Data FOR RETURN SIMULATION.xlsx'
        
        try:
            rdata = pd.read_excel(file_path, sheet_name='Data', header=2, skiprows=[3, 4])
            
            # Strip whitespace from column names and remove duplicates
            rdata.columns = rdata.columns.str.strip()
            rdata = rdata.loc[:, ~rdata.columns.duplicated(keep='first')]

            # Add 'Ticker' column if missing
            if 'Ticker' not in rdata.columns and 'Ticker-Region' in rdata.columns:
                rdata['Ticker'] = rdata['Ticker-Region'].str.split('-').str[0].str.strip()

            # Apply sector restriction logic
            if restrict_fossil_fuels:
                industry_col = 'FactSet Industry'
                if industry_col in rdata.columns:
                    rdata[industry_col] = rdata[industry_col].astype(str).str.lower()
                    fossil_keywords = ['oil', 'gas', 'coal', 'energy', 'fossil']
                    mask = rdata[industry_col].apply(lambda x: not any(kw in x for kw in fossil_keywords))
                    rdata = rdata[mask]
                else:
                    print("Warning: 'FactSet Industry' column not found. Fossil fuel filtering skipped.")

            # Ensure 'Year' column is present
            if 'Year' not in rdata.columns and 'Date' in rdata.columns:
                rdata['Year'] = pd.to_datetime(rdata['Date']).dt.year

            # Filter out rows with missing essential data (same as Supabase filtering)
            rdata = _filter_essential_data(rdata)
            
            print(f"Successfully loaded {len(rdata)} records from Excel file after filtering")
            return rdata
            
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            raise


def _standardize_column_names(df):
    """
    Standardize column names from Supabase to match existing code expectations.
    Converts snake_case (typical in databases) to the format expected by existing code.
    """
    # Import column mapping from config
    try:
        from config import COLUMN_DISPLAY_NAMES
        column_mapping = COLUMN_DISPLAY_NAMES
    except ImportError:
        # Fallback mapping if config is not available
        column_mapping = {
            # Core columns
            'id': 'ID',
            'security_name': 'Security Name',
            'ticker_region': 'Ticker-Region',
            'russell_2000_port_weight': 'Russell 2000 Port. Weight',
            'ending_price': 'Ending Price',
            'market_capitalization': 'Market Capitalization',
            'date': 'Date',
            'year': 'Year',
            'ticker': 'Ticker',
            'factset_industry': 'FactSet Industry',
            'scotts_sector_5': "Scott's Sector (5)",
            
            # Factor columns
            'roe_using_9_30_data': 'ROE using 9/30 Data',
            'roa_using_9_30_data': 'ROA using 9/30 Data',
            'momentum_12m_pct': '12-Mo Momentum %',
            'momentum_6m_pct': '6-Mo Momentum %',
            'momentum_1m_pct': '1-Mo Momentum %',
            'price_to_book_using_9_30_data': 'Price to Book Using 9/30 Data',
            'next_fy_earns_p': 'Next FY Earns/P',
            'price_vol_1yr_pct': '1-Yr Price Vol %',
            'accruals_assets': 'Accruals/Assets',
            'roa_pct': 'ROA %',
            'asset_growth_1yr_pct': '1-Yr Asset Growth %',
            'capex_growth_1yr_pct': '1-Yr CapEX Growth %',
            'book_price': 'Book/Price',
            'next_year_return_pct': "Next-Year's Return %",
            'next_year_active_return_pct': "Next-Year's Active Return %",
            
            # Additional financial columns
            'ni_millions': 'NI, $Millions',
            'opcf_millions': 'OpCF, $Millions',
            'latest_assets_millions': 'Latest Assets, $Millions',
            'prior_year_assets_millions': "Prior Year's Assets, $Millions",
            'book_value_per_share': 'Book Value Per Share $',
            'capex_millions': 'CapEx, $Millions',
            'prior_year_capex_millions': "Prior Year's CapEx, $Millions",
            'earnings_surprise_pct': 'Earnings Surprise %',
            'earnings_reported_last': 'Earnings Reported Last',
            'avg_daily_3mo_volume_mills': 'Avg Daily 3-Mo Volume Mills $'
        }
    
    # Apply column name mapping
    df = df.rename(columns=column_mapping)
    
    # Ensure required columns exist (with fallback logic)
    if 'Ticker' not in df.columns:
        if 'Ticker-Region' in df.columns:
            df['Ticker'] = df['Ticker-Region'].str.split('-').str[0].str.strip()
        elif 'ticker_region' in df.columns:
            df['Ticker'] = df['ticker_region'].str.split('-').str[0].str.strip()
    
    if 'Year' not in df.columns:
        if 'Date' in df.columns:
            df['Year'] = pd.to_datetime(df['Date']).dt.year
        elif 'date' in df.columns:
            df['Year'] = pd.to_datetime(df['date']).dt.year
    
    # Ensure Ticker-Region exists if we have ticker_region in lowercase
    if 'Ticker-Region' not in df.columns and 'ticker_region' in df.columns:
        df['Ticker-Region'] = df['ticker_region']
    
    return df


def _filter_essential_data(df):
    """
    Filter out rows with missing essential data like pricing information.
    """
    if df.empty:
        return df
        
    initial_count = len(df)
    
    # Remove rows where Ending Price is missing or invalid
    if 'Ending Price' in df.columns:
        df = df[df['Ending Price'].notna() & (df['Ending Price'] > 0)]
    
    # Remove rows where Ticker is missing
    if 'Ticker' in df.columns:
        df = df[df['Ticker'].notna() & (df['Ticker'] != '') & (df['Ticker'] != '--')]
    elif 'Ticker-Region' in df.columns:
        df = df[df['Ticker-Region'].notna() & (df['Ticker-Region'] != '') & (df['Ticker-Region'] != '--')]
    
    # Remove rows where Date/Year is missing
    if 'Year' in df.columns:
        df = df[df['Year'].notna()]
    elif 'Date' in df.columns:
        df = df[df['Date'].notna()]
    
    filtered_count = len(df)
    removed_count = initial_count - filtered_count
    
    if removed_count > 0:
        print(f"Filtered out {removed_count} rows with missing essential data (price, ticker, or date)")
    
    return df

 

"""
Note: A duplicate Supabase loading implementation existed below which directly
queried a hard-coded table and bypassed the standardized column mapping. It has
been removed to ensure a single, robust data-loading path via SupabaseDataClient
above. The supported entry point is load_data(restrict_fossil_fuels=False,
use_supabase=True, table_name='All').
"""

class MarketObject():
    def __init__(self, data, t, verbosity=1):
        """
        data(DataFrame): Market data with columns like 'Ticker', 'Ending Price', etc.
        t (int): Year of market data.
        verbosity (int): Controls level of printed output. 0 = silent, 1 = normal, 2+ = verbose.
        """
        # Remove duplicated column names
        data.columns = data.columns.str.strip()
        data = data.loc[:, ~data.columns.duplicated(keep='first')]

        # Ensure 'Ticker' and 'Year' columns are present
        if 'Ticker' not in data.columns and 'Ticker-Region' in data.columns:
            data['Ticker'] = data['Ticker-Region'].str.split('-').str[0].str.strip()
        if 'Year' not in data.columns and 'Date' in data.columns:
            data['Year'] = pd.to_datetime(data['Date']).dt.year

        # Define relevant columns
        available_factors = [
            'ROE using 9/30 Data', 'ROA using 9/30 Data', '12-Mo Momentum %', '1-Mo Momentum %',
            'Price to Book Using 9/30 Data', 'Next FY Earns/P', '1-Yr Price Vol %', 'Accruals/Assets',
            'ROA %', '1-Yr Asset Growth %', '1-Yr CapEX Growth %', 'Book/Price',
            "Next-Year's Return %", "Next-Year's Active Return %"
        ]
        keep_cols = ['Ticker', 'Ending Price', 'Year', '6-Mo Momentum %'] + available_factors

        # Filter and clean data
        data = data[[col for col in keep_cols if col in data.columns]].copy()
        data.replace({'--': None, 'N/A': None, '#N/A': None, '': None}, inplace=True)
        
        # Convert numeric columns to proper numeric types
        numeric_columns = ['Ending Price'] + [col for col in available_factors if col in data.columns]
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')

        # Set 'Ticker' as the index for faster lookups
        data.set_index('Ticker', inplace=True)

        self.stocks = data
        self.t = t
        self.verbosity = verbosity

    def get_price(self, ticker):
        try:
            price = self.stocks.at[ticker, 'Ending Price']
            # Check if price is valid (not NaN, not None, and positive)
            if pd.isna(price) or price is None or price <= 0:
                if self.verbosity >= 2:
                    print(f"{ticker} - invalid price ({price}) for {self.t} - SKIPPING")
                return None
            return price
        except KeyError:
            if self.verbosity >= 2:
                print(f"{ticker} - not found in market data for {self.t} - SKIPPING")
            return None

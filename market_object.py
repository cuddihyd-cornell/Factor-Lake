import pandas as pd
import numpy as np
import os

def load_data(restrict_fossil_fuels=False, use_supabase=False, table_name='FR2000 Annual Quant Data'):
    rdata = None
    # Try Supabase if requested or credentials are set
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    if use_supabase or (supabase_url and supabase_key):
        try:
            from supabase_client import load_supabase_data
            print("Loading data from Supabase...")
            rdata = load_supabase_data(table_name)
        except Exception as e:
            print(f"Supabase load failed: {e}. Falling back to Excel.")
    if rdata is None:
        file_path = '/content/drive/My Drive/Cayuga Fund Factor Lake/FR2000 Annual Quant Data FOR RETURN SIMULATION.xlsx'
        print("Loading data from Excel file...")
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

    return rdata

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
        data.replace({'--': None}, inplace=True)

        # Set 'Ticker' as the index for faster lookups
        data.set_index('Ticker', inplace=True)

        self.stocks = data
        self.t = t
        self.verbosity = verbosity

    def get_price(self, ticker):
        try:
            return self.stocks.at[ticker, 'Ending Price']
        except KeyError:
            if self.verbosity >= 2:
                print(f"{ticker} - not found in market data for {self.t} - SKIPPING")
            return None

import pandas as pd
import numpy as np
from supabase import create_client
from dotenv import load_dotenv
import os

# Load .env from repo folder
load_dotenv("/content/Factor-Lake/.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

### CREATING FUNCTION TO LOAD DATA ###
def load_data(restrict_fossil_fuels=False):
    # Fetch data from Supabase
    response = supabase.table("FR2000 Annual Quant Data").select("*").execute()
    rdata = pd.DataFrame(response.data)
    # 🔍 Add this line to inspect the columns
    # print("Supabase columns:", rdata.columns.tolist())

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

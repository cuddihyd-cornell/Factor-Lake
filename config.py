"""
Configuration file for Supabase connection.
Set your Supabase credentials here or use environment variables.
"""

# Supabase Configuration
# Option 1: Set these directly (not recommended for production)
SUPABASE_URL = ""  # Your Supabase project URL
SUPABASE_KEY = ""  # Your Supabase anon key or service role key

# Option 2: Use environment variables (recommended)
# Set these in your environment:
# export SUPABASE_URL="your_project_url"
# export SUPABASE_KEY="your_anon_key"

# Database Configuration
DEFAULT_TABLE_NAME = "All"  # Default table name for market data

# All available columns from your Excel data
ALL_COLUMNS = [
    'id',
    'security_name',
    'ticker_region', 
    'russell_2000_port_weight',
    'ending_price',
    'market_capitalization',
    'roe_using_9_30_data',
    'roa_using_9_30_data',
    'price_to_book_using_9_30_data',
    'date',
    'next_fy_earns_p',
    'momentum_12m_pct',
    'momentum_6m_pct', 
    'momentum_1m_pct',
    'price_vol_1yr_pct',
    'accruals_assets',
    'roa_pct',
    'asset_growth_1yr_pct',
    'capex_growth_1yr_pct',
    'book_price',
    'next_year_return_pct',
    'next_year_active_return_pct',
    'factset_industry',
    'scotts_sector_5',
    'ni_millions',
    'opcf_millions',
    'latest_assets_millions',
    'prior_year_assets_millions',
    'book_value_per_share',
    'capex_millions',
    'prior_year_capex_millions',
    'earnings_surprise_pct',
    'earnings_reported_last',
    'avg_daily_3mo_volume_mills'
]

# Factor columns only (the ones used for portfolio construction)
FACTOR_COLUMNS = [
    'roe_using_9_30_data',
    'roa_using_9_30_data', 
    'momentum_12m_pct',
    'momentum_6m_pct',
    'momentum_1m_pct',
    'price_to_book_using_9_30_data',
    'next_fy_earns_p',
    'price_vol_1yr_pct',
    'accruals_assets',
    'roa_pct',
    'asset_growth_1yr_pct',
    'capex_growth_1yr_pct',
    'book_price',
    'next_year_return_pct',
    'next_year_active_return_pct'
]

# Complete column name mappings from database schema to Excel column names
COLUMN_DISPLAY_NAMES = {
    # Core identification columns
    'id': 'ID',
    'security_name': 'Security Name',
    'ticker_region': 'Ticker-Region',
    'russell_2000_port_weight': 'Russell 2000 Port. Weight',
    'ending_price': 'Ending Price',
    'market_capitalization': 'Market Capitalization',
    'date': 'Date',
    'factset_industry': 'FactSet Industry',
    'scotts_sector_5': "Scott's Sector (5)",
    
    # Factor columns (used for portfolio construction)
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
    
    # Financial data columns
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
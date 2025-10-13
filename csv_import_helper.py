"""
CSV Import Helper for Supabase Migration

This script helps you import your Excel data into Supabase.
Run this after setting up your Supabase database with the correct schema.
"""

import pandas as pd
import os
from supabase_client import create_supabase_client
import numpy as np
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_excel_data(file_path, sheet_name='Data'):
    """
    Load and clean Excel data for Supabase import.
    
    Args:
        file_path: Path to your Excel file
        sheet_name: Name of the Excel sheet (default: 'Data')
    
    Returns:
        pandas.DataFrame: Cleaned data ready for Supabase
    """
    logger.info(f"Loading Excel file: {file_path}")
    
    # Load Excel data with the same parameters as your original code
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=2, skiprows=[3, 4])
    
    # Clean column names
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.duplicated(keep='first')]
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Convert column names to database-friendly format (snake_case)
    column_mapping = {
        'ID': 'id',
        'Security Name': 'security_name',
        'Ticker-Region': 'ticker_region',
        'Russell 2000 Port. Weight': 'russell_2000_port_weight',
        'Ending Price': 'ending_price',
        'Market Capitalization': 'market_capitalization',
        'ROE using 9/30 Data': 'roe_using_9_30_data',
        'ROA using 9/30 Data': 'roa_using_9_30_data',
        'Price to Book Using 9/30 Data': 'price_to_book_using_9_30_data',
        'Date': 'date',
        'Next FY Earns/P': 'next_fy_earns_p',
        '12-Mo Momentum %': 'momentum_12m_pct',
        '6-Mo Momentum %': 'momentum_6m_pct',
        '1-Mo Momentum %': 'momentum_1m_pct',
        '1-Yr Price Vol %': 'price_vol_1yr_pct',
        'Accruals/Assets': 'accruals_assets',
        'ROA %': 'roa_pct',
        '1-Yr Asset Growth %': 'asset_growth_1yr_pct',
        '1-Yr CapEX Growth %': 'capex_growth_1yr_pct',
        'Book/Price': 'book_price',
        "Next-Year's Return %": 'next_year_return_pct',
        "Next-Year's Active Return %": 'next_year_active_return_pct',
        'FactSet Industry': 'factset_industry',
        "Scott's Sector (5)": 'scotts_sector_5',
        'NI, $Millions': 'ni_millions',
        'OpCF, $Millions': 'opcf_millions',
        'Latest Assets, $Millions': 'latest_assets_millions',
        "Prior Year's Assets, $Millions": 'prior_year_assets_millions',
        'Book Value Per Share $': 'book_value_per_share',
        'CapEx, $Millions': 'capex_millions',
        "Prior Year's CapEx, $Millions": 'prior_year_capex_millions',
        'Earnings Surprise %': 'earnings_surprise_pct',
        'Earnings Reported Last': 'earnings_reported_last',
        'Avg Daily 3-Mo Volume Mills $': 'avg_daily_3mo_volume_mills'
    }
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    # Clean data
    # Replace common null representations
    df = df.replace({'--': None, '': None, '#N/A': None, 'N/A': None})
    
    # Convert date column to proper datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # Convert numeric columns
    numeric_columns = [
        'russell_2000_port_weight', 'ending_price', 'market_capitalization',
        'roe_using_9_30_data', 'roa_using_9_30_data', 'price_to_book_using_9_30_data',
        'next_fy_earns_p', 'momentum_12m_pct', 'momentum_6m_pct', 'momentum_1m_pct',
        'price_vol_1yr_pct', 'accruals_assets', 'roa_pct', 'asset_growth_1yr_pct',
        'capex_growth_1yr_pct', 'book_price', 'next_year_return_pct', 'next_year_active_return_pct',
        'ni_millions', 'opcf_millions', 'latest_assets_millions', 'prior_year_assets_millions',
        'book_value_per_share', 'capex_millions', 'prior_year_capex_millions',
        'earnings_surprise_pct', 'avg_daily_3mo_volume_mills'
    ]
    
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Remove rows where all important columns are null
    key_columns = ['ticker_region', 'ending_price', 'date']
    df = df.dropna(subset=[col for col in key_columns if col in df.columns], how='all')
    
    logger.info(f"After cleaning: {len(df)} rows remain")
    return df

def upload_to_supabase(df, table_name='market_data', batch_size=1000):
    """
    Upload DataFrame to Supabase in batches.
    
    Args:
        df: pandas DataFrame to upload
        table_name: Name of Supabase table
        batch_size: Number of records per batch
    """
    logger.info(f"Starting upload to Supabase table '{table_name}'")
    
    # Create Supabase client
    client = create_supabase_client()
    
    # Convert DataFrame to records
    records = df.to_dict('records')
    
    # Convert NaN values to None for JSON serialization
    for record in records:
        for key, value in record.items():
            if pd.isna(value) or (isinstance(value, float) and np.isnan(value)):
                record[key] = None
    
    total_records = len(records)
    logger.info(f"Uploading {total_records} records in batches of {batch_size}")
    
    # Upload in batches
    successful_uploads = 0
    failed_uploads = 0
    
    for i in range(0, total_records, batch_size):
        batch = records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total_records + batch_size - 1) // batch_size
        
        try:
            response = client.client.table(table_name).insert(batch).execute()
            successful_uploads += len(batch)
            logger.info(f"✅ Batch {batch_num}/{total_batches} uploaded successfully ({len(batch)} records)")
            
        except Exception as e:
            failed_uploads += len(batch)
            logger.error(f"❌ Batch {batch_num}/{total_batches} failed: {e}")
            
            # Try uploading records individually to identify problematic ones
            logger.info("Trying individual record uploads for this batch...")
            for j, record in enumerate(batch):
                try:
                    client.client.table(table_name).insert([record]).execute()
                    successful_uploads += 1
                    failed_uploads -= 1
                except Exception as record_error:
                    logger.error(f"Failed to upload record {i+j}: {record_error}")
                    logger.error(f"Problematic record: {record}")
    
    logger.info(f"Upload complete: {successful_uploads} successful, {failed_uploads} failed")
    return successful_uploads, failed_uploads

def main():
    """Main function to run the import process."""
    
    # Check environment variables
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        print("❌ Please set SUPABASE_URL and SUPABASE_KEY environment variables")
        print("Example:")
        print("os.environ['SUPABASE_URL'] = 'https://your-project.supabase.co'")
        print("os.environ['SUPABASE_KEY'] = 'your-anon-key'")
        return
    
    # File path - update this to match your file location
    excel_file_path = input("Enter path to your Excel file: ").strip()
    
    if not os.path.exists(excel_file_path):
        print(f"❌ File not found: {excel_file_path}")
        return
    
    try:
        # Load and clean data
        df = clean_excel_data(excel_file_path)
        
        print(f"\nData preview:")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("\nFirst few rows:")
        print(df.head())
        
        # Ask for confirmation
        proceed = input("\nProceed with upload? (y/N): ").strip().lower()
        if proceed != 'y':
            print("Upload cancelled")
            return
        
        # Upload to Supabase
        successful, failed = upload_to_supabase(df)
        
        print(f"\n🎉 Import complete!")
        print(f"✅ Successful: {successful} records")
        print(f"❌ Failed: {failed} records")
        
        if failed > 0:
            print("\n💡 If you had failures, check the log messages above for details.")
            print("Common issues: data type mismatches, constraint violations, or connection timeouts.")
        
    except Exception as e:
        logger.error(f"Import failed: {e}")
        print(f"\n❌ Import failed: {e}")

if __name__ == "__main__":
    main()
"""
Supabase client for Factor Lake data management.
Handles connection, authentication, and data queries.
"""
import os
import pandas as pd
from supabase import create_client, Client
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseDataClient:
    """Client for interacting with Supabase database for Factor Lake data."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (or set SUPABASE_URL env var)
            key: Supabase anon/service key (or set SUPABASE_KEY env var)
        """
        self.url = url or os.getenv('SUPABASE_URL')
        self.key = key or os.getenv('SUPABASE_KEY')
        
        if not self.url or not self.key:
            raise ValueError(
                "Supabase URL and key required. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables or pass them directly to constructor."
            )
        
        try:
            self.client: Client = create_client(self.url, self.key)
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def load_market_data(self, 
                        table_name: str = 'market_data',
                        year_filter: Optional[int] = None,
                        restrict_fossil_fuels: bool = False) -> pd.DataFrame:
        """
        Load market data from Supabase table.
        
        Args:
            table_name: Name of the table containing market data
            year_filter: Optional year to filter data (if None, loads all years)
            restrict_fossil_fuels: Whether to exclude fossil fuel companies
            
        Returns:
            DataFrame with market data
        """
        try:
            # Build query
            query = self.client.table(table_name).select("*")
            
            # Add year filter if specified
            if year_filter:
                query = query.eq('year', year_filter)
            
            # Execute query
            response = query.execute()
            
            if not response.data:
                logger.warning(f"No data found in table '{table_name}'")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(response.data)
            
            # Apply fossil fuel restrictions if needed
            if restrict_fossil_fuels:
                df = self._apply_fossil_fuel_filter(df)
            
            # Clean and standardize column names
            df = self._clean_dataframe(df)
            
            logger.info(f"Loaded {len(df)} records from Supabase")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from Supabase: {e}")
            raise
    
    def _apply_fossil_fuel_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply fossil fuel industry filter to dataframe."""
        industry_col = 'factset_industry'  # Adjust column name as needed
        
        if industry_col not in df.columns:
            logger.warning(f"Column '{industry_col}' not found. Fossil fuel filtering skipped.")
            return df
        
        # Convert to lowercase for case-insensitive matching
        df[industry_col] = df[industry_col].astype(str).str.lower()
        
        fossil_keywords = ['oil', 'gas', 'coal', 'energy', 'fossil']
        
        # Create mask to exclude fossil fuel companies
        mask = df[industry_col].apply(
            lambda x: not any(kw in str(x) for kw in fossil_keywords) 
            if pd.notna(x) else True
        )
        
        filtered_df = df[mask].copy()
        logger.info(f"Filtered out {len(df) - len(filtered_df)} fossil fuel companies")
        
        return filtered_df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize DataFrame format."""
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        
        # Replace common null representations
        df.replace({'--': None, '': None}, inplace=True)
        
        # Ensure ticker column exists
        if 'ticker' not in df.columns and 'ticker_region' in df.columns:
            df['ticker'] = df['ticker_region'].str.split('-').str[0].str.strip()
        
        # Ensure year column exists
        if 'year' not in df.columns and 'date' in df.columns:
            df['year'] = pd.to_datetime(df['date']).dt.year
        
        return df
    
    def get_available_years(self, table_name: str = 'market_data') -> list:
        """Get list of available years in the database."""
        try:
            response = self.client.table(table_name).select("year").execute()
            years = sorted(set(row['year'] for row in response.data if row['year']))
            logger.info(f"Available years: {years}")
            return years
        except Exception as e:
            logger.error(f"Error getting available years: {e}")
            return []
    
    def get_available_factors(self, table_name: str = 'market_data') -> list:
        """Get list of available factor columns in the database."""
        try:
            # Get first row to examine columns
            response = self.client.table(table_name).select("*").limit(1).execute()
            
            if not response.data:
                return []
            
            # Filter for factor-related columns (adjust as needed based on your schema)
            all_columns = list(response.data[0].keys())
            factor_columns = [col for col in all_columns 
                            if any(keyword in col.lower() for keyword in 
                                 ['momentum', 'roe', 'roa', 'price', 'book', 'earns', 'vol', 
                                  'accrual', 'growth', 'return'])]
            
            logger.info(f"Available factors: {factor_columns}")
            return factor_columns
            
        except Exception as e:
            logger.error(f"Error getting available factors: {e}")
            return []


def create_supabase_client(url: Optional[str] = None, key: Optional[str] = None) -> SupabaseDataClient:
    """
    Factory function to create a SupabaseDataClient instance.
    
    Args:
        url: Supabase project URL (optional if set in env vars)
        key: Supabase key (optional if set in env vars)
        
    Returns:
        Configured SupabaseDataClient instance
    """
    return SupabaseDataClient(url, key)
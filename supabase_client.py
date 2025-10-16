import os
import pandas as pd
from supabase import create_client, Client

def load_supabase_data(table_name='FR2000 Annual Quant Data'):
    """
    Loads data from a Supabase table and returns it as a pandas DataFrame.
    Credentials are read from environment variables or Colab userdata.
    Uses pagination to load all records.
    """
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        try:
            from google.colab import userdata
            supabase_url = userdata.get('SUPABASE_URL')
            supabase_key = userdata.get('SUPABASE_KEY')
        except Exception:
            pass
    if not supabase_url or not supabase_key:
        raise RuntimeError('Supabase credentials not set. Please set SUPABASE_URL and SUPABASE_KEY.')
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Paginate through all records
    page_size = 1000
    offset = 0
    all_rows = []
    
    print(f"Loading data from Supabase table '{table_name}'...")
    
    while True:
        # Fetch a page of data
        response = supabase.table(table_name).select('*').range(offset, offset + page_size - 1).execute()
        
        batch = response.data if hasattr(response, 'data') else response
        
        if not batch:
            break
        
        all_rows.extend(batch)
        print(f"Loaded {len(all_rows)} records so far...")
        
        # If we got fewer records than page_size, we're done
        if len(batch) < page_size:
            break
        
        offset += page_size
    
    print(f"Total records loaded: {len(all_rows)}")
    
    # Debug: Print columns in the data
    if all_rows:
        print(f"DEBUG: Columns in Supabase table (first 20): {list(all_rows[0].keys())[:20]}")
        print(f"DEBUG: Total columns in table: {len(all_rows[0].keys())}")
    
    return pd.DataFrame(all_rows)
    
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
            # Fetch all rows with pagination to avoid default page limits
            page_size = 1000
            offset = 0
            rows = []

            # If a year filter is provided, filter by Date range on the server if possible
            # Note: Column name uses exact case as in the DB schema ("Date")
            base_query = self.client.table(table_name).select("*")
            if year_filter:
                start_date = f"{year_filter}-01-01"
                end_date = f"{year_filter}-12-31"
                base_query = base_query.gte('Date', start_date).lte('Date', end_date)

            # Use ID ordering for deterministic pagination if available
            # If "ID" column doesn't exist, pagination will still work without ordering
            try:
                base_query = base_query.order('ID', desc=False)
            except Exception:
                pass

            while True:
                try:
                    response = base_query.range(offset, offset + page_size - 1).execute()
                except Exception as e:
                    logger.error(f"Error during Supabase pagination (offset={offset}): {e}")
                    raise

                batch = response.data or []
                if not batch:
                    break
                rows.extend(batch)
                if len(batch) < page_size:
                    break
                offset += page_size

            if not rows:
                logger.warning(f"No data found in table '{table_name}' with the given filters")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(rows)
            
            # Apply fossil fuel restrictions if needed
            if restrict_fossil_fuels:
                df = self._apply_fossil_fuel_filter(df)
            
            # Clean and standardize column names
            df = self._clean_dataframe(df)
            
            # Filter out rows with missing essential data
            df = self._filter_incomplete_data(df)
            
            logger.info(f"Loaded {len(df)} records from Supabase after filtering")
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from Supabase: {e}")
            raise
    
    def _apply_fossil_fuel_filter(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply fossil fuel industry filter to dataframe."""
        import re
        possible_cols = ['FactSet_Industry', 'factset_industry', 'FactSet Industry']
        industry_col = None
        for col in possible_cols:
            if col in df.columns:
                industry_col = col
                break
        if industry_col is None:
            logger.warning(f"Column 'FactSet_Industry' not found. Fossil fuel filtering skipped.")
            return df
        # Excluded industries (normalized)
        excluded_industries = [
            "integratedoil",
            "oilfieldservicesequipment",
            "oilgasproduction",
            "coal",
            "oilrefiningmarketing"
        ]
        # Normalize function: lowercase and remove non-alphanumeric
        def normalize(s):
            return re.sub(r'[^a-z0-9]', '', str(s).lower())
        # Apply normalization to both data and excluded list
        industry_norm = df[industry_col].apply(normalize)
        excluded_norm = set(excluded_industries)
        mask = ~industry_norm.isin(excluded_norm)
        filtered_df = df[mask].copy()
        removed_count = len(df) - len(filtered_df)
        logger.info(f"Filtered out {removed_count} fossil fuel companies from {len(df)} total records")
        return filtered_df
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize DataFrame format."""
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        
        # Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated(keep='first')]
        
        # Replace common null representations
        df.replace({'--': None, '': None, 'N/A': None, '#N/A': None, 'NULL': None, 'null': None}, inplace=True)
        
        # Ensure ticker column exists
        if 'ticker' not in df.columns and 'ticker_region' in df.columns:
            df['ticker'] = df['ticker_region'].str.split('-').str[0].str.strip()
        
        # Ensure year column exists
        if 'year' not in df.columns and 'date' in df.columns:
            df['year'] = pd.to_datetime(df['date']).dt.year
        
        return df
    
    def _filter_incomplete_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter out rows with missing essential data after querying.
        Removes rows where critical columns like price data are missing.
        """
        initial_count = len(df)
        
        # Define essential columns that must have valid data
        essential_columns = []
        
        # Check for price columns (try multiple possible names)
        price_columns = ['Ending Price', 'ending_price', 'Price']
        for col in price_columns:
            if col in df.columns:
                essential_columns.append(col)
                break
        
        # Check for ticker columns
        ticker_columns = ['Ticker', 'ticker', 'Ticker-Region', 'ticker_region']
        for col in ticker_columns:
            if col in df.columns:
                essential_columns.append(col)
                break
        
        # Check for date/year columns
        date_columns = ['Date', 'date', 'Year', 'year']
        for col in date_columns:
            if col in df.columns:
                essential_columns.append(col)
                break
        
        if not essential_columns:
            logger.warning("No essential columns found for filtering")
            return df
        
        # Filter out rows where essential columns are null or invalid
        for col in essential_columns:
            if col in df.columns:
                # Remove rows where the column is null, empty, or contains invalid values
                if df[col].dtype in ['float64', 'int64']:
                    # For numeric columns, remove null, inf, or zero values (for price)
                    if 'price' in col.lower() or 'Price' in col:
                        df = df[df[col].notna() & (df[col] > 0) & (df[col] != float('inf'))]
                    else:
                        df = df[df[col].notna() & (df[col] != float('inf'))]
                else:
                    # For text columns, remove null or empty strings
                    df = df[df[col].notna() & (df[col] != '') & (df[col] != '--')]
        
        filtered_count = len(df)
        removed_count = initial_count - filtered_count
        
        if removed_count > 0:
            logger.info(f"Filtered out {removed_count} rows with missing essential data")
            logger.info(f"Remaining records: {filtered_count}")
        
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



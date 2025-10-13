# Supabase Migration Guide

This guide helps you migrate from Excel to Supabase for your Factor Lake system.

## 1. Supabase Setup

### Create Supabase Project
1. Go to [supabase.com](https://supabase.com) and create an account
2. Create a new project
3. Note your project URL and anon key from the API settings

### Set Environment Variables
In your Google Colab, add these environment variables:

```python
import os
os.environ['SUPABASE_URL'] = 'your_supabase_project_url'
os.environ['SUPABASE_KEY'] = 'your_supabase_anon_key'
```

## 2. Database Schema Setup

Create a table called `market_data` with the following structure based on your Excel columns:

```sql
CREATE TABLE market_data (
    -- Primary key (auto-generated)
    id SERIAL PRIMARY KEY,
    
    -- Core identification columns
    security_name VARCHAR(255),
    ticker_region VARCHAR(100),
    russell_2000_port_weight DECIMAL(10,6),
    ending_price DECIMAL(12,4),
    market_capitalization BIGINT,
    date DATE,
    year INTEGER, -- Derived from date
    ticker VARCHAR(50), -- Derived from ticker_region
    
    -- Industry and sector classification
    factset_industry TEXT,
    scotts_sector_5 VARCHAR(100),
    
    -- Factor columns (used for portfolio construction)
    roe_using_9_30_data DECIMAL(8,4),
    roa_using_9_30_data DECIMAL(8,4),
    price_to_book_using_9_30_data DECIMAL(8,4),
    next_fy_earns_p DECIMAL(8,4),
    momentum_12m_pct DECIMAL(8,4),
    momentum_6m_pct DECIMAL(8,4),
    momentum_1m_pct DECIMAL(8,4),
    price_vol_1yr_pct DECIMAL(8,4),
    accruals_assets DECIMAL(8,4),
    roa_pct DECIMAL(8,4),
    asset_growth_1yr_pct DECIMAL(8,4),
    capex_growth_1yr_pct DECIMAL(8,4),
    book_price DECIMAL(8,4),
    next_year_return_pct DECIMAL(8,4),
    next_year_active_return_pct DECIMAL(8,4),
    
    -- Additional financial data columns
    ni_millions DECIMAL(12,2),
    opcf_millions DECIMAL(12,2),
    latest_assets_millions DECIMAL(15,2),
    prior_year_assets_millions DECIMAL(15,2),
    book_value_per_share DECIMAL(10,4),
    capex_millions DECIMAL(12,2),
    prior_year_capex_millions DECIMAL(12,2),
    earnings_surprise_pct DECIMAL(8,4),
    earnings_reported_last VARCHAR(50),
    avg_daily_3mo_volume_mills DECIMAL(12,2)
);

-- Add indexes for performance
CREATE INDEX idx_ticker ON market_data(ticker);
CREATE INDEX idx_year ON market_data(year);
CREATE INDEX idx_ticker_year ON market_data(ticker, year);
CREATE INDEX idx_date ON market_data(date);
CREATE INDEX idx_factset_industry ON market_data(factset_industry);

-- Add triggers to auto-populate derived columns
CREATE OR REPLACE FUNCTION populate_derived_columns()
RETURNS TRIGGER AS $$
BEGIN
    -- Extract ticker from ticker_region
    NEW.ticker = SPLIT_PART(NEW.ticker_region, '-', 1);
    
    -- Extract year from date
    IF NEW.date IS NOT NULL THEN
        NEW.year = EXTRACT(year FROM NEW.date);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_populate_derived_columns
    BEFORE INSERT OR UPDATE ON market_data
    FOR EACH ROW EXECUTE FUNCTION populate_derived_columns();
```

## 3. Data Migration

### Option A: Manual Upload via Supabase Dashboard
1. Export your Excel data to CSV
2. Use Supabase dashboard to import CSV data
3. Map columns appropriately

### Option B: Programmatic Upload (Python script)
```python
import pandas as pd
from supabase_client import create_supabase_client

# Load your Excel data
excel_data = pd.read_excel('your_file.xlsx', sheet_name='Data', header=2, skiprows=[3, 4])

# Clean and prepare data
# ... (your existing cleaning logic)

# Upload to Supabase
client = create_supabase_client()
records = excel_data.to_dict('records')

# Upload in batches to avoid timeout
batch_size = 1000
for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]
    client.client.table('market_data').insert(batch).execute()
    print(f"Uploaded batch {i//batch_size + 1}")
```

## 4. Updated Google Colab Code

Replace your existing Colab code with this updated version:

```python
import subprocess
import matplotlib.pyplot as plt
import sys
import os
%matplotlib inline

### SET SUPABASE CREDENTIALS ###
os.environ['SUPABASE_URL'] = 'your_supabase_project_url_here'
os.environ['SUPABASE_KEY'] = 'your_supabase_anon_key_here'

### MOUNTING GOOGLE DRIVE (optional now - only needed for fallback) ###
from google.colab import drive
drive.mount('/content/drive')

### FUNCTION TO REDIRECT UNNECESSARY OUTPUT & ERRORS TO A LOG FILE ###
def run_command(command, log_file_path):
    with open(log_file_path, 'w') as log_file:
        result = subprocess.run(command, shell=True, stdout=log_file, stderr=log_file)
        if result.returncode != 0:
            print(f'Error occurred. See log file: {log_file_path}')
            sys.exit(1)

### CLONING GITHUB REPOSITORY ###
!rm -rf /content/Factor-Lake
clone_command = 'git clone https://github.com/cuddihyd-cornell/Factor-Lake.git'
run_command(clone_command, '/content/clone_repo_log.txt')

### CHECKOUT SUPABASE BRANCH ###
!git -C /content/Factor-Lake checkout supa

### INSTALLING REQUIREMENTS (now includes supabase) ###
!pip install -r /content/Factor-Lake/requirements.txt

### IMPORT AND RUN main() DIRECTLY ###
sys.path.insert(0, '/content/Factor-Lake')
from main import main
main()
```

## 5. Testing the Migration

1. Start with a small subset of your data in Supabase
2. Test the connection and data loading
3. Verify that factor calculations work correctly
4. Compare results with your Excel-based system
5. Gradually migrate more data

## 6. Benefits of Supabase Migration

- **Performance**: Faster queries, especially with indexes
- **Scalability**: Handle larger datasets easily  
- **Concurrent Access**: Multiple users can access the same data
- **Real-time Updates**: Data can be updated in real-time
- **API Access**: Direct REST API access to your data
- **Backup & Recovery**: Automated backups
- **Security**: Row-level security and authentication

## 7. Troubleshooting

### Common Issues:
1. **Connection Error**: Check your URL and key
2. **Column Name Mismatch**: Verify column mapping in `config.py`
3. **Data Type Issues**: Ensure numeric columns are properly formatted
4. **Performance**: Add indexes for frequently queried columns

### Fallback Mode:
If Supabase is unavailable, the system automatically falls back to Excel mode.
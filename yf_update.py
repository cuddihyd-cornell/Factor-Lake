from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

def update_market_data(table_name: str, ticker: str, start_default: str = "2002-01-01"):
    """
    Incrementally update a Supabase table with new Yahoo Finance data.

    Args:
        table_name (str): Supabase table name.
        ticker (str): Yahoo Finance ticker symbol.
        start_default (str): Default start date if the table is empty.
    
    Behavior:
        - Finds the latest date in Supabase.
        - Downloads new daily data from Yahoo Finance.
        - Filters out duplicates.
        - Inserts new rows in safe batches.
    """
    client = create_supabase_client()
    
    # Determine start date
    try:
        response = (
            client.client.table(table_name)
            .select("Date")
            .order("Date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            latest_date_str = response.data[0]["Date"]
            latest_date = pd.to_datetime(latest_date_str)
            start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Latest date in {table_name}: {latest_date.Date()}")
        else:
            start_date = start_default
            print(f"No existing data in {table_name}, downloading full history.")
    except Exception as e:
        print(f"Error getting latest date: {e}")
        start_date = start_default

    end_date = datetime.today().strftime("%Y-%m-%d")

    # Download new data
    print(f"Fetching {ticker} data from {start_date} to {end_date}...")
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)

    if data.empty:
        print("No new data available.")
        return

    df = data[["Close"]].reset_index()
  
    df["ticker"] = TICKER
    df["Date"] = pd.to_datetime(df["Date"]).dt.date.astype(str)

    df = df[["Date", "ticker", "Close"]]

    # Deduplicate (skip dates already in Supabase)
    try:
        existing_resp = client.client.table(table_name).select("Date").execute()
        existing_dates = {row["Date"] for row in existing_resp.data}
        before = len(df)
        df = df[~df["Date"].isin(existing_dates)]
        print(f"Filtered out {before - len(df)} duplicates; {len(df)} new rows remain.")
    except Exception as e:
        print(f"Warning: Could not fetch existing dates ({e}); inserting all rows.")

    if len(df) == 0:
        print("No new rows to insert.")
        return

    # Insert in batches
    rows = df.to_dict(orient="records")
    batch_size = 500
    total_inserted = 0

    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            client.client.table(table_name).insert(batch).execute()
            total_inserted += len(batch)
            time.sleep(0.3)
        except Exception as e:
            print(f"Error inserting batch {i // batch_size + 1}: {e}")
            time.sleep(2)

    print(f" Successfully inserted {total_inserted} new rows into {table_name}.")

# Sample
# update_market_data("RUT_yf", "^RUT")


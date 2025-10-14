from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import time

def update_market_data(table_name: str, ticker: str, start_default: str = "2002-01-01"):
    """
    Simplified version for debugging:
    - Prints raw yfinance data
    - Prints final dataframe
    - Prints exact rows being inserted
    """
    client = create_supabase_client()
    
    # Determine start date
    try:
        response = (
            client.client.table(table_name)
            .select("date")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            latest_date_str = response.data[0]["date"]
            latest_date = pd.to_datetime(latest_date_str)
            start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Latest date in {table_name}: {latest_date.date()}")
        else:
            start_date = start_default
            print(f"No existing data in {table_name}, downloading full history.")
    except Exception as e:
        print(f"Error getting latest date: {e}")
        start_date = start_default

    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"\nFetching {ticker} data from {start_date} to {end_date}...\n")

    # --- Download from Yahoo Finance ---
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)

    # Print raw yfinance data
    print("=== Raw yfinance output ===")
    print(data.tail(10))  # print the last 10 rows
    print("===========================\n")

    if data.empty:
        print("No new data available.")
        return

    # --- Transform data into desired structure ---
    df = data[["Close"]].reset_index()
    df["ticker"] = ticker
    df.rename(columns={"Date": "date", "Close": "close"}, inplace=True)
    df = df[["date", "ticker", "close"]]

    # Print transformed DataFrame
    print("=== Transformed DataFrame ===")
    print(df.head(10))
    print("=============================\n")

    # --- Prepare rows to insert ---
    rows = df.to_dict(orient="records")

    print("=== Rows about to insert ===")
    for r in rows:
        print(r)
    print("=============================\n")

    # --- Try insert ---
    try:
        response = client.client.table(table_name).insert(rows).execute()
        print(f"✅ Successfully inserted {len(rows)} rows into {table_name}")
    except Exception as e:
        print(f"❌ Insert error: {e}")

# Example call:
# update_market_data("RUT_yf", "^RUT")

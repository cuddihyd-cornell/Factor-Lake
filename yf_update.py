from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def update_market_data(table_name: str, ticker: str):
    """
    Update existing Supabase table with new Yahoo Finance data.
    - Checks if table exists.
    - Gets latest available date.
    - Downloads only missing data from Yahoo Finance.
    - Flattens columns to avoid tuple keys.
    - Inserts new rows (assumes table already exists).
    """
    client = create_supabase_client()

    # Step 1 — Verify table existence
    try:
        client.client.table(table_name).select("date").limit(1).execute()
        print(f"Verified table '{table_name}' exists.")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"Table '{table_name}' does not exist. Please create it first.")
            return
        else:
            print(f"Error verifying table: {e}")
            return

    # Step 2 — Find latest date
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
            print(f"No data in '{table_name}', cannot perform incremental update.")
            return
    except Exception as e:
        print(f"Error fetching latest date: {e}")
        return

    # Step 3 — Download new data
    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"Fetching {ticker} data from {start_date} to {end_date}...")

    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"yfinance error: {e}")
        return

    if data.empty:
        print("No new data available.")
        return

    # Step 4 — Flatten MultiIndex columns
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(c) for c in col if c]).strip() for col in data.columns.values]

    # Step 5 — Identify correct Close column dynamically
    close_col = [c for c in data.columns if c.lower().startswith("close")][0]

    # Step 6 — Prepare DataFrame for insert
    df = data.reset_index()[["Date", close_col]].rename(columns={"Date": "date", close_col: "close"})
    df["ticker"] = ticker
    df = df[["date", "ticker", "close"]]

    print(f"New rows fetched: {len(df)}")
    print(df.head())

    # Step 7 — Insert new rows
    rows = df.to_dict(orient="records")
    try:
        client.client.table(table_name).insert(rows).execute()
        print(f"Successfully inserted {len(rows)} new rows into '{table_name}'.")
    except Exception as e:
        print(f"Insert error: {e}")

    print("Update complete.")

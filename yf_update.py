from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import json
import functools
print = functools.partial(print, flush=True)

def update_market_data(table_name: str, ticker: str) -> None:
    """
    Update an existing Supabase table with new Yahoo Finance data.

    Behavior:
    - Uses existing Supabase connection (create_supabase_client)
    - Fetches last available date from Supabase
    - Downloads only new daily data for the given ticker
    - Performs UPSERT on (date, ticker)
    - Falls back to INSERT if unique constraint not found
    - Prints debug info and results
    """

    print(f"\nConnecting to Supabase for table '{table_name}'...")
    client = create_supabase_client()
    print("Connected.\n")

    # Verify table
    try:
        client.client.table(table_name).select("date").limit(1).execute()
        print(f"Verified table '{table_name}' exists.\n")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"Table '{table_name}' does not exist. Please create it manually first.")
            return
        print(f"Unexpected error while checking table existence: {e}")
        return

    # Get latest date
    try:
        resp = (
            client.client.table(table_name)
            .select("date")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        if resp.data and len(resp.data) > 0:
            latest_date = pd.to_datetime(resp.data[0]["date"])
            start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Latest date in {table_name}: {latest_date.date()}")
        else:
            print(f"Table '{table_name}' is empty — nothing to update.")
            return
    except Exception as e:
        print(f"Error determining latest date: {e}")
        return

    # Download new data
    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"\nFetching {ticker} data from {start_date} to {end_date}...\n")

    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"yfinance error: {e}")
        return

    if data.empty:
        print("No new data available. Table already up to date.")
        return

    # Clean & transform
    data = data.reset_index()
    if "Close" not in data.columns:
        print(f"'Close' column not found in yfinance data: {data.columns.tolist()}")
        return

    df = data[["Date", "Close"]].copy()
    df.rename(columns={"Date": "date", "Close": "close"}, inplace=True)
    df["ticker"] = ticker
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df["close"] = df["close"].astype(float)
    df = df[["date", "ticker", "close"]]

    # Debug preview
    print("========== NEW DATA PREVIEW ==========")
    print(df.head(10))
    print(f"Total new rows: {len(df)}")
    print("======================================\n")

    rows = df.to_dict(orient="records")

    print("========== ROW STRUCTURE CHECK ==========")
    print(json.dumps(rows[:3], indent=2, ensure_ascii=False))
    print("=========================================\n")

    # UPSERT
    print(f"Attempting UPSERT into '{table_name}' on conflict ['date', 'ticker'] ...")
    try:
        resp = client.client.table(table_name).upsert(rows, on_conflict=["date", "ticker"]).execute()
        print("UPSERT completed successfully.\n")
        print("Response data preview:", resp.data[:5] if resp.data else "(no data returned)")
    except Exception as e:
        print(f"Upsert failed: {e}")
        print("Falling back to plain INSERT (no on_conflict)...")
        try:
            resp = client.client.table(table_name).insert(rows).execute()
            print("INSERT completed successfully.")
            print("Response data preview:", resp.data[:5] if resp.data else "(no data returned)")
        except Exception as inner:
            print(f"Insert also failed: {inner}")
    print()

    # Final preview
    print(f"Preview of latest 5 rows from '{table_name}':")
    try:
        preview = client.client.table(table_name).select("*").order("date", desc=True).limit(5).execute()
        print(json.dumps(preview.data or [], indent=2, ensure_ascii=False))
    except Exception as e:
        print("Preview fetch failed:", e)

    print("\nUpdate complete.\n")

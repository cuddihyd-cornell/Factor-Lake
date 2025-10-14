from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def update_market_data(table_name: str, ticker: str, start_default: str = "2002-01-01"):
    """
    Update existing Supabase table with new Yahoo Finance data.

    Behavior:
    - Checks if table exists (no creation).
    - Finds latest date and fetches only missing data.
    - Inserts new rows (no duplicates if UNIQUE(date, ticker) exists).
    """

    client = create_supabase_client()

    # --- Step 1: Check if table exists ---
    try:
        client.client.table(table_name).select("date").limit(1).execute()
        print(f"✅ Verified table '{table_name}' exists.\n")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"❌ Table '{table_name}' does not exist. Please create it manually first.")
            return
        else:
            print(f"⚠️ Unexpected error while checking table existence: {e}")
            return

    # --- Step 2: Determine start date ---
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
            print(f"⚠️ No existing data found in '{table_name}', cannot perform incremental update.")
            return
    except Exception as e:
        print(f"❌ Error determining latest date: {e}")
        return

    # --- Step 3: Download new data ---
    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"\n📡 Fetching {ticker} data from {start_date} to {end_date}...\n")

    try:
        # Explicitly disable auto_adjust to avoid tuple columns
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"❌ yfinance download error: {e}")
        return

    if data.empty:
        print("✅ No new data available. Table is already up to date.")
        return

    # --- Step 4: Normalize columns (extra safety) ---
    data.columns = data.columns.map(str)  # ensure no tuple or non-string column names

    # --- Step 5: Transform new data ---
    df = data[["Close"]].reset_index()
    df.rename(columns={"Date": "date", "Close": "close"}, inplace=True)
    df["ticker"] = ticker
    df = df[["date", "ticker", "close"]]

    print("=== New data preview (first 10 rows) ===")
    print(df.head(10))
    print(f"\nTotal new rows to insert: {len(df)}")
    print("========================================\n")

    # --- Step 6: Insert new rows ---
    rows = df.to_dict(orient="records")
    try:
        client.client.table(table_name).insert(rows).execute()
        print(f"✅ Successfully inserted {len(rows)} new rows into '{table_name}'.")
    except Exception as e:
        print(f"❌ Insert error: {e}")

    print("Update complete.\n")

# Example usage
# update_market_data("RUT_yf", "^RUT")

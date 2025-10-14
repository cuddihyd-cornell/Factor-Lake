from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def update_market_data(table_name: str, ticker: str, start_default: str = "2002-01-01"):
    """
    Update existing Supabase table with new Yahoo Finance data.

    - Assumes 'date' is the PRIMARY KEY (single-column)
    - Fetches only missing rows
    - Uses UPSERT (on_conflict=['date']) for safe updating
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

    # --- Step 2: Find latest date ---
    try:
        response = (
            client.client.table(table_name)
            .select("date")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            latest_date_str = response.data[0]["date"]
            latest_date = pd.to_datetime(latest_date_str)
            start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Latest date in {table_name}: {latest_date.date()}")
        else:
            print(f"⚠️ No existing data in '{table_name}', downloading from default start date.")
            start_date = start_default
    except Exception as e:
        print(f"❌ Error determining latest date: {e}")
        start_date = start_default

    # --- Step 3: Download from yfinance ---
    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"\n📡 Fetching {ticker} data from {start_date} to {end_date}...\n")

    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"❌ yfinance download error: {e}")
        return

    if data.empty:
        print("✅ No new data available. Table is already up to date.")
        return

    # --- Step 4: Flatten columns and clean ---
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(c) for c in col if c]) for col in data.columns]
    else:
        data.columns = data.columns.astype(str)

    df = data.reset_index()[["Date", "Close"]]
    df.rename(columns={"Date": "date", "Close": "close"}, inplace=True)
    df["ticker"] = ticker
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df["close"] = df["close"].astype(float)
    df = df[["date", "ticker", "close"]]

    print("=== New data preview (first 10 rows) ===")
    print(df.head(10))
    print(f"\nTotal new rows: {len(df)}")
    print("========================================\n")

    # --- Step 5: Safe UPSERT ---
    df.columns = df.columns.map(str)
    rows = df.to_dict(orient="records")

    try:
        client.client.table(table_name).upsert(rows, on_conflict=["date"]).execute()
        print(f"✅ Successfully upserted {len(rows)} rows into '{table_name}' (on_conflict=['date']).")
    except Exception as e:
        print(f"❌ Upsert error: {e}")

    print("Update complete.\n")

# Example usage
# update_market_data("RUT_yf", "^RUT")

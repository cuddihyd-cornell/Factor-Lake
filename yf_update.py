from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def update_market_data(table_name: str, ticker: str, start_default: str = "2002-01-01"):
    """
    FINAL stable version:
    - Works with single PK 'date'
    - Fetches only missing data from Yahoo Finance
    - Cleans any tuple keys (columns, index, dict)
    - Uses UPSERT on 'date'
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
            latest_date = pd.to_datetime(response.data[0]["date"])
            start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Latest date in {table_name}: {latest_date.date()}")
        else:
            print(f"⚠️ No existing data in '{table_name}', starting full download.")
            start_date = start_default
    except Exception as e:
        print(f"❌ Error determining latest date: {e}")
        start_date = start_default

    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"\n📡 Fetching {ticker} data from {start_date} to {end_date}...\n")

    # --- Step 3: Download data ---
    try:
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            progress=False,
            auto_adjust=False
        )
    except Exception as e:
        print(f"❌ yfinance error: {e}")
        return

    if data.empty:
        print("✅ No new data available. Table already up to date.")
        return

    # --- Step 4: Flatten all tuples in columns & index ---
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(c) for c in col if c]) for col in data.columns]
    else:
        data.columns = [str(c) for c in data.columns]

    # Flatten index names if any
    if isinstance(data.index, pd.MultiIndex):
        data.index = ['_'.join(map(str, idx)) for idx in data.index]
    else:
        data.index = data.index.map(str)

    # --- Step 5: Build DataFrame ---
    df = data.reset_index()

    # Ensure the Date column exists
    date_col = None
    for col in df.columns:
        if col.lower() == "date":
            date_col = col
            break
    if not date_col:
        print(f"❌ Could not find date column in yfinance data. Columns: {df.columns.tolist()}")
        return

    close_col = None
    for col in df.columns:
        if "close" in col.lower():
            close_col = col
            break
    if not close_col:
        print(f"❌ Could not find close column in yfinance data. Columns: {df.columns.tolist()}")
        return

    df = df[[date_col, close_col]].rename(columns={date_col: "date", close_col: "close"})
    df["ticker"] = ticker
    df = df[["date", "ticker", "close"]]
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df["close"] = df["close"].astype(float)

    print("=== New data preview ===")
    print(df.head())
    print("========================\n")

    # --- Step 6: Convert to pure-JSON records safely ---
    def make_json_safe(val):
        if isinstance(val, (tuple, list, set)):
            return str(val)
        if pd.isna(val):
            return None
        return val

    rows = []
    for rec in df.to_dict(orient="records"):
        clean_rec = {str(k): make_json_safe(v) for k, v in rec.items()}
        rows.append(clean_rec)

    print(f"Prepared {len(rows)} clean rows for upload.\n")

    # --- Step 7: UPSERT on 'date' ---
    try:
        client.client.table(table_name).upsert(rows, on_conflict=["date"]).execute()
        print(f"✅ Successfully upserted {len(rows)} rows into '{table_name}'.")
    except Exception as e:
        print(f"❌ Upsert error: {e}")

    print("✅ Update complete.\n")

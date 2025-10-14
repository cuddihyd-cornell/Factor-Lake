from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def update_market_data(table_name: str, ticker: str, start_default: str = "2002-01-01"):
    """
    Fully safe updater for an existing Supabase table.
    Handles any MultiIndex/tupple column issues from yfinance.
    """

    client = create_supabase_client()

    # --- Verify table existence ---
    try:
        client.client.table(table_name).select("date").limit(1).execute()
        print(f"✅ Verified table '{table_name}' exists.\n")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"❌ Table '{table_name}' does not exist. Please create it manually first.")
        else:
            print(f"⚠️ Unexpected error while checking table existence: {e}")
        return

    # --- Get latest date ---
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
            print(f"⚠️ No existing data found in '{table_name}', cannot perform incremental update.")
            return
    except Exception as e:
        print(f"❌ Error determining latest date: {e}")
        return

    # --- Fetch new data ---
    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"\n📡 Fetching {ticker} data from {start_date} to {end_date}...\n")

    try:
        data = yf.download(ticker, start=start_date, end=end_date,
                           progress=False, auto_adjust=False)
    except Exception as e:
        print(f"❌ yfinance download error: {e}")
        return

    if data.empty:
        print("✅ No new data available. Table is already up to date.")
        return

    # --- STEP: Flatten any multiindex columns and reset index cleanly ---
    # Force simple index
    data = data.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(c) for c in col if c]) for col in data.columns]
    else:
        data.columns = [str(c) for c in data.columns]
    data = data.reset_index()
    data.columns = [str(c) for c in data.columns]

    # --- Sanity check ---
    print("🧩 Columns after flattening:", data.columns.tolist())

    # --- Transform into final df ---
    if "Close" not in data.columns:
        possible = [c for c in data.columns if "Close" in c]
        if possible:
            close_col = possible[0]
            print(f"⚠️ Using alternate close column: {close_col}")
        else:
            print(f"❌ 'Close' column not found. Available columns: {data.columns.tolist()}")
            return
    else:
        close_col = "Close"

    df = data[["Date", close_col]].copy()
    df.rename(columns={"Date": "date", close_col: "close"}, inplace=True)
    df["ticker"] = ticker
    df = df[["date", "ticker", "close"]]

    # Convert everything to proper types
    df["date"] = pd.to_datetime(df["date"]).dt.date.astype(str)
    df["close"] = df["close"].astype(float)

    print("\n=== Final dataframe preview ===")
    print(df.tail())
    print("===============================\n")

    # --- Convert safely to JSON-serializable records ---
    df.columns = df.columns.map(str)
    rows = []
    for r in df.to_dict(orient="records"):
        clean = {}
        for k, v in r.items():
            clean[str(k)] = None if pd.isna(v) else v
        rows.append(clean)

    # --- Insert ---
    try:
        client.client.table(table_name).insert(rows).execute()
        print(f"✅ Successfully inserted {len(rows)} new rows into '{table_name}'.")
    except Exception as e:
        print(f"❌ Insert error: {e}")

    print("Update complete.\n")

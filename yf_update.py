from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def update_market_data(table_name: str, ticker: str):
    """
    Update an existing Supabase table with new Yahoo Finance data.
    Fetches data after the most recent date and inserts new rows.
    """

    client = create_supabase_client()

    # Verify that the target table exists
    try:
        client.client.table(table_name).select("date").limit(1).execute()
        print(f"Table '{table_name}' verified.")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"Table '{table_name}' does not exist. Please create it first.")
            return
        print(f"Error verifying table: {e}")
        return

    # Retrieve the most recent date in the table
    try:
        response = (
            client.client.table(table_name)
            .select("date")
            .order("date", desc=True)
            .limit(1)
            .execute()
        )
        if response.data and len(response.data) > 0:
            latest_date = pd.to_datetime(response.data[0]["date"])
            start_date = (latest_date + timedelta(days=1)).strftime("%Y-%m-%d")
            print(f"Latest record date: {latest_date.date()}")
        else:
            print(f"No existing data in '{table_name}'. Nothing to update.")
            return
    except Exception as e:
        print(f"Error fetching latest date: {e}")
        return

    # Download only the missing data from Yahoo Finance
    end_date = datetime.today().strftime("%Y-%m-%d")
    print(f"Fetching data for {ticker} from {start_date} to {end_date}...")

    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return

    if data.empty:
        print("No new data available.")
        return

    # Flatten MultiIndex columns if present (yfinance sometimes returns tuples)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(c) for c in col if c]).strip() for col in data.columns.values]

    # Identify the correct close column dynamically
    close_col = [c for c in data.columns if c.lower().startswith("close")][0]

    # Prepare data for insertion
    df = data.reset_index()[["Date", close_col]].rename(columns={"Date": "date", close_col: "close"})
    df["ticker"] = ticker
    df = df[["date", "ticker", "close"]]

    rows = df.to_dict(orient="records")

    # Insert the new records into the Supabase table
    try:
        client.client.table(table_name).insert(rows).execute()
        print(f"Inserted {len(rows)} new rows into '{table_name}'.")
    except Exception as e:
        print(f"Insert error: {e}")

    print("Update complete.")

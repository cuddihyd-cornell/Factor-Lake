from supabase_client import create_supabase_client
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def update_market_data(table_name: str, ticker: str):
    """
    Update existing Supabase table with new Yahoo Finance data.
    
    - Verifies that the table exists.
    - Finds the latest date and downloads only missing records.
    - Inserts new rows if available.
    """
    client = create_supabase_client()

    # Verify table existence
    try:
        client.client.table(table_name).select("date").limit(1).execute()
        print(f"Table '{table_name}' verified.")
    except Exception as e:
        if "does not exist" in str(e) or "not found" in str(e):
            print(f"Table '{table_name}' does not exist. Please create it first.")
            return
        else:
            print(f"Error checking table existence: {e}")
            return

    # Get latest record date
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
            print(f"No existing data found in '{table_name}'.")
            return
    except Exception as e:
        print(f"Error retrieving latest date: {e}")
        return

    # Download new data
    end_date = datetime.today().strftime("%Y-%m-%d")
    if start_date == end_date:
        next_day = (pd.to_datetime(end_date) + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = next_day
        print(f"Fetching today's ({start_date}) data — only available after the market closes.")
    else:
        print(f"Fetching data for {ticker} from {start_date} to {end_date}...")

    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    except Exception as e:
        print(f"Download error: {e}")
        return

    if data.empty:
        print("No new data available. Table is up to date.")
        return

    # Flatten columns if MultiIndex
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = ['_'.join([str(c) for c in col if c]).strip() for col in data.columns.values]

    # Transform
    close_col = [c for c in data.columns if "Close" in c][0]
    df = data[[close_col]].reset_index()
    df.rename(columns={close_col: "close", "Date": "date"}, inplace=True)
    df["ticker"] = ticker
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")  # <- FIX: ensure string
    df = df[["date", "ticker", "close"]]

    # Insert new data
    try:
        rows = df.to_dict(orient="records")
        client.client.table(table_name).insert(rows).execute()
        print(f"Update complete. {len(rows)} new records inserted into '{table_name}'.")
    except Exception as e:
        print(f"Insert error: {e}")



def show_latest_records(table_name: str):
    """
    Display the 10 newest records from a Supabase table.

    - Connects using existing Supabase client.
    - Orders by date descending.
    - Displays results as a DataFrame if available.
    """
    client = create_supabase_client()

    try:
        response = (
            client.client.table(table_name)
            .select("*")
            .order("date", desc=True)
            .limit(10)
            .execute()
        )

        if not response.data:
            print(f"No data found in '{table_name}'.")
        else:
            df = pd.DataFrame(response.data)
            print(f"Showing 10 newest records from '{table_name}':\n")
            print(df)
    except Exception as e:
        print(f"Error fetching records: {e}")

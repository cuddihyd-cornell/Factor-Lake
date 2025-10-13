"""
Simple Supabase connection test - will prompt for credentials if not in environment.
"""
import os

def test_connection():
    # Check if credentials are in environment
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url:
        url = input("Enter your Supabase project URL: ").strip()
        os.environ['SUPABASE_URL'] = url
        
    if not key:
        key = input("Enter your Supabase anon key: ").strip()
        os.environ['SUPABASE_KEY'] = key
    
    print("Testing connection...")
    
    try:
        from supabase_client import create_supabase_client
        client = create_supabase_client()
        print(" Successfully connected to Supabase!")
        
        # Test a simple query
        response = client.client.table('All').select('*').limit(1).execute()
        
        if response.data:
            print(f" Successfully queried data! Found records in 'All' table.")
            print(f"Sample record columns: {list(response.data[0].keys())}")
            return True
        else:
            print("  Connected but no data found in 'All' table.")
            return False
            
    except Exception as e:
        print(f" Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
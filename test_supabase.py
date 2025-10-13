"""
Test script for Supabase integration.
Run this to verify your Supabase connection and data loading works correctly.
"""

import os
import sys
from supabase_client import create_supabase_client
from market_object import load_data
import pandas as pd

def test_supabase_connection():
    """Test basic Supabase connection."""
    print("Testing Supabase connection...")
    
    try:
        client = create_supabase_client()
        print("✅ Successfully connected to Supabase")
        return True
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {e}")
        return False

def test_data_loading():
    """Test data loading functionality."""
    print("\nTesting data loading...")
    
    try:
        # Test loading data from Supabase
        data = load_data(use_supabase=True, restrict_fossil_fuels=False)
        
        if data.empty:
            print("⚠️  No data loaded - check if your table has data")
            return False
        
        print(f"✅ Successfully loaded {len(data)} records")
        print(f"   Columns: {list(data.columns)}")
        print(f"   Years available: {sorted(data['Year'].unique()) if 'Year' in data.columns else 'Year column not found'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return False

def test_fossil_fuel_filter():
    """Test fossil fuel filtering."""
    print("\nTesting fossil fuel filtering...")
    
    try:
        # Load data with and without fossil fuel restriction
        data_all = load_data(use_supabase=True, restrict_fossil_fuels=False)
        data_filtered = load_data(use_supabase=True, restrict_fossil_fuels=True)
        
        if data_all.empty:
            print("⚠️  No data available to test filtering")
            return False
        
        print(f"✅ All data: {len(data_all)} records")
        print(f"✅ Filtered data: {len(data_filtered)} records")
        
        if len(data_filtered) < len(data_all):
            print(f"✅ Fossil fuel filter working: removed {len(data_all) - len(data_filtered)} companies")
        else:
            print("⚠️  Fossil fuel filter may not be working (no records filtered)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test fossil fuel filtering: {e}")
        return False

def test_factor_columns():
    """Test that required factor columns are available."""
    print("\nTesting factor columns...")
    
    try:
        data = load_data(use_supabase=True, restrict_fossil_fuels=False)
        
        if data.empty:
            print("⚠️  No data available to test columns")
            return False
        
        # Expected factor columns
        expected_factors = [
            'ROE using 9/30 Data', 'ROA using 9/30 Data', '12-Mo Momentum %',
            '6-Mo Momentum %', '1-Mo Momentum %', 'Price to Book Using 9/30 Data',
            'Next FY Earns/P', '1-Yr Price Vol %', 'Accruals/Assets', 'ROA %',
            '1-Yr Asset Growth %', '1-Yr CapEX Growth %', 'Book/Price',
            "Next-Year's Return %", "Next-Year's Active Return %"
        ]
        
        available_factors = [col for col in expected_factors if col in data.columns]
        missing_factors = [col for col in expected_factors if col not in data.columns]
        
        print(f"✅ Available factors ({len(available_factors)}): {available_factors}")
        if missing_factors:
            print(f"⚠️  Missing factors ({len(missing_factors)}): {missing_factors}")
        
        return len(available_factors) > 0
        
    except Exception as e:
        print(f"❌ Failed to test factor columns: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running Supabase Integration Tests")
    print("=" * 50)
    
    # Check environment variables
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        print("❌ SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        print("   Add these to your environment or Colab notebook:")
        print("   os.environ['SUPABASE_URL'] = 'your_project_url'")
        print("   os.environ['SUPABASE_KEY'] = 'your_anon_key'")
        return
    
    # Run tests
    tests = [
        test_supabase_connection,
        test_data_loading, 
        test_fossil_fuel_filter,
        test_factor_columns
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 50)
    print("🏁 Test Results Summary")
    print(f"✅ Passed: {sum(results)}/{len(results)} tests")
    
    if all(results):
        print("🎉 All tests passed! Your Supabase integration is ready.")
    else:
        print("⚠️  Some tests failed. Check the errors above and your Supabase setup.")

if __name__ == "__main__":
    main()
"""
Local test script for Factor Lake with Supabase integration.
Run this in VS Code to test the code locally without Colab.
"""

import os
import sys
import matplotlib.pyplot as plt

# Set matplotlib to use non-interactive backend for testing
plt.switch_backend('Agg')

# Set Supabase credentials
os.environ['SUPABASE_URL'] = 'https://ozusfgnnzanaxpcfidbm.supabase.co'
os.environ['SUPABASE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im96dXNmZ25uemFuYXhwY2ZpZGJtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ2NDE4MTcsImV4cCI6MjA1MDIxNzgxN30.4LN6_PyVKM3BdygFWVdeZrirAVA_AxZFyNAA'

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import and run main
from main import main

if __name__ == "__main__":
    print("Starting Factor Lake (Local Test)...")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[0]}")
    print("-" * 50)
    
    try:
        main()
        print("\n" + "=" * 50)
        print("Test completed successfully!")
    except Exception as e:
        print("\n" + "=" * 50)
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

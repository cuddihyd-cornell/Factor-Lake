"""
Simple launcher script for the Streamlit application
"""
import subprocess
import sys
import os

def main():
    """Launch the Streamlit application"""
    print("=" * 60)
    print("Starting Factor-Lake Portfolio Analysis")
    print("=" * 60)
    print("\nThe application will open in your default browser...")
    print("Press Ctrl+C to stop the server\n")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    streamlit_app = os.path.join(script_dir, "streamlit_app.py")
    
    # Check if streamlit_app.py exists
    if not os.path.exists(streamlit_app):
        print(f"Error: streamlit_app.py not found at {streamlit_app}")
        sys.exit(1)
    
    try:
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            streamlit_app,
            "--server.port", "8501",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        print("Thank you for using Factor-Lake!")
    except Exception as e:
        print(f"\nError running Streamlit: {e}")
        print("\nMake sure Streamlit is installed:")
        print("  pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()

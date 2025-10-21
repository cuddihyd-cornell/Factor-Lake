"""
User input for Supabase data source selection
"""

def get_supabase_preference():
    """
    Ask the user if they want to load data from Supabase or Excel.
    
    Returns:
        bool: True if user wants Supabase, False for Excel fallback
    """
    while True:
        response = input("\nDo you want to load data from Supabase? (Yes/No): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Invalid input. Please enter 'Yes' or 'No'.")


def get_data_loading_verbosity():
    """
    Ask the user if they want to see data loading progress messages.
    
    Returns:
        bool: True to show loading messages, False to hide them
    """
    while True:
        response = input("\nShow data loading progress? (Yes/No): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Invalid input. Please enter 'Yes' or 'No'.")


def get_excel_file_path():
    """
    Ask the user for the Excel file path if not using Supabase.
    
    Returns:
        str: Path to Excel file
    """
    print("\nPlease provide the path to your Excel file:")
    print("Example: C:\\Users\\YourName\\Documents\\data.xlsx")
    file_path = input("File path: ").strip()
    
    # Remove quotes if user wrapped the path in quotes
    if file_path.startswith('"') and file_path.endswith('"'):
        file_path = file_path[1:-1]
    if file_path.startswith("'") and file_path.endswith("'"):
        file_path = file_path[1:-1]
    
    return file_path

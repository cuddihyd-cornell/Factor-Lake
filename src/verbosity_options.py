VERBOSITY_OPTIONS = {
    1: "Summary Only",
    2: "Year-by-Year Results",
    3: "Debug (Everything)"
}

def get_verbosity_level():
    print("\nSelect output verbosity level:")
    for key, value in VERBOSITY_OPTIONS.items():
        print(f"{key}. {value}")
    choice = input("Enter your choice (1-3): ")
    try:
        choice = int(choice)
        if choice in VERBOSITY_OPTIONS:
            print(f"\nVerbosity set to: {VERBOSITY_OPTIONS[choice]}")
            return choice
        else:
            print("Invalid selection. Defaulting to Summary Only.")
            return 1
    except ValueError:
        print("Invalid input, defaulting to Summary Only.")
        return 1

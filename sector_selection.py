SECTORS = [
    "Consumer",
    "Technology",
    "Financials",
    "Industrials",
    "Healthcare",
]


def get_sector_selection():
    """
    Prompt user to select sectors to include.

    Flow:
    - Show numbered list (1-5)
    - Ask: How many sectors? (ALL or 1-5)
    - If ALL, return the full sector list
    - Else, prompt for that many sector indices.

    Returns:
    - list[str]: Selected sector names (empty list means all sectors)
    """
    print("\nAvailable sectors:")
    for i, s in enumerate(SECTORS, start=1):
        print(f"{i}. {s}")

    while True:
        resp = input("\nHow many sectors to include? (ALL, 1,2,3,4,5): ").strip()
        if resp.lower() == "all":
            print("Selecting ALL sectors.")
            return SECTORS.copy()
        try:
            n = int(resp)
            if n < 1 or n > len(SECTORS):
                raise ValueError
            break
        except ValueError:
            print("Invalid input. Enter ALL or an integer 1-5.")

    chosen = []
    used = set()
    for idx in range(1, n + 1):
        while True:
            try:
                sel = int(input(f"Select sector #{idx} by index (1-{len(SECTORS)}): "))
                if sel < 1 or sel > len(SECTORS):
                    raise ValueError
                if sel in used:
                    print("Already selected. Choose a different index.")
                    continue
                used.add(sel)
                chosen.append(SECTORS[sel - 1])
                break
            except ValueError:
                print("Please enter a valid integer within range.")
    print(f"Selected sectors: {', '.join(chosen)}")
    return chosen

def get_fossil_fuel_restriction():
    response = input("\nRestrict fossil fuel companies? (Yes/No): ").strip().lower()
    if response in ["yes", "y"]:
        print("Fossil fuel restriction enabled.")
        return True
    else:
        print("No fossil fuel restriction applied.")

        return False

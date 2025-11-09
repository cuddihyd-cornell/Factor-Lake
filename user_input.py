import factor_function

def get_factors(available_factors):
    # Display the lists of available factors with index
    print("\nAvailable factors: ")
    for i in range(len(available_factors)):
        print(f"{i + 1}. {available_factors[i]}")
    
    # Get the number of factors user wants to use
    while(True):
        try:
            num = int(input("How many factors do you want to use?\n"))
            if num > len(available_factors):
                raise Exception
        except ValueError:
            print("Please input an integer.")
            continue
        except Exception:
            print("Number is out of range.")
            continue
        else:
            break
    
    # Get the selected factors
    factors = []
    for i in range(num):
        while True:
            try:
                selected_factor = int(input(f"Please input the index of factor {i + 1}: \n"))
                if selected_factor > len(available_factors):
                    raise Exception
            except ValueError:
                print("Please input an integer.")
                continue
            except Exception:
                print("Index is out of range.")
                continue
            else:
                break
    
        name = available_factors[selected_factor - 1]
        match name:
            case "ROE using 9/30 Data":
                factors.append((factor_function.ROE(), name))
            case "ROA using 9/30 Data":
                factors.append((factor_function.ROA(), name))
            case "6-Mo Momentum %":
                factors.append((factor_function.Momentum6m(), name))
            case "12-Mo Momentum %":
                factors.append((factor_function.Momentum12m(), name))
            case "1-Mo Momentum %":
                factors.append((factor_function.Momentum1m(), name))
            case "Price to Book Using 9/30 Data":
                factors.append((factor_function.P2B(), name))
            case "Next FY Earns/P":
                factors.append((factor_function.NextFYrEarns(), name))
            case "1-Yr Price Vol %":
                factors.append((factor_function.OneYrPriceVol(), name))
            case "Accruals/Assets":
                factors.append((factor_function.AccrualsAssets(), name))
            case "ROA %":
                factors.append((factor_function.ROAPercentage(), name))
            case "1-Yr Asset Growth %":
                factors.append((factor_function.OneYrAssetGrowth(), name))
            case "1-Yr CapEX Growth %":
                factors.append((factor_function.OneYrCapEXGrowth(), name))
            case "Book/Price":
                factors.append((factor_function.BookPrice(), name))
            case _:
                print(f"factor {name} is not available.")
    
    return factors


def get_top_bottom_options(selected_factor_names):
    """
    Ask the user if they'd like to plot top/bottom N% portfolios and gather options.

    Returns:
        None if user doesn't want the plot, otherwise a dict with keys:
        - percent (int)
        - show_bottom (bool)
        - chosen_index (int) index into selected_factor_names
    """
    if not selected_factor_names:
        print("No selected factors available for top/bottom analysis.")
        return None

    resp = input("Would you like to plot Top/Bottom N% portfolios for a factor? (y/n): ").strip().lower()
    if resp not in ('y', 'yes'):
        return None

    # Percent input
    while True:
        try:
            pct = int(input("Enter percentage N (1-100) for Top/Bottom selection (e.g. 10): "))
            if pct < 1 or pct > 100:
                raise ValueError
            break
        except ValueError:
            print("Please enter an integer between 1 and 100.")

    show_bottom = False
    if pct < 100:
        sb = input(f"Also show Bottom {pct}%? (y/n): ").strip().lower()
        show_bottom = sb in ('y', 'yes')

    # Choose which selected factor to analyze
    print("Selected factors:")
    for i, name in enumerate(selected_factor_names):
        print(f"{i + 1}. {name}")

    while True:
        try:
            choice = int(input(f"Choose factor index to analyze (1-{len(selected_factor_names)}): "))
            if choice < 1 or choice > len(selected_factor_names):
                raise ValueError
            break
        except ValueError:
            print("Please enter a valid index number.")

    return {
        'percent': pct,
        'show_bottom': show_bottom,
        'chosen_index': choice - 1
    }
    

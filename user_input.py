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

def get_top_bottom_plot_choice(default_n=10):
    """
    Ask the user (centralized input module) whether to plot Top n% / Bottom n%.
    Returns a tuple: (plot_top_n: bool, n_percent: int, include_bottom: bool)
    """
    try:
        ans = input("Plot top n% / bottom n% comparison? (y/n) [n]: ").strip().lower() or "n"
    except Exception:
        ans = "n"
    plot_top_n = ans in ("y", "yes")
    if not plot_top_n:
        return False, default_n, False

    try:
        n_input = input(f"Enter percent n (e.g. 10 for top 10%) [{default_n}]: ").strip() or str(default_n)
        n_percent = int(n_input)
    except Exception:
        n_percent = default_n

    try:
        inc = input("Include bottom n% as well? (y/n) [y]: ").strip().lower() or "y"
    except Exception:
        inc = "y"
    include_bottom = inc in ("y", "yes")

    return True, n_percent, include_bottom


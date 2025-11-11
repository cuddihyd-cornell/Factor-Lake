import factor_function
# add near existing argparse setup
import argparse

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
    

def build_parser():
    parser = argparse.ArgumentParser(description="Factor-Lake runtime options")
    # You can add other existing args here if you already had them.

    # CHANGED: allow omission so we can prompt
    parser.add_argument(
        "--weighting",
        choices=["equal", "mcap"],
        help="Weighting scheme: 'equal' or 'mcap'. If omitted, you'll be prompted."
    )
    parser.add_argument(
        "--top-percent",
        type=float,
        default=10.0,
        help="Top percent of names to select (default: 10)."
    )
    parser.add_argument(
        "--restrict-fossil-fuels",
        action="store_true",
        help="Exclude fossil-fuel industries from holdings if set."
    )
    parser.add_argument(
        "--verbosity",
        type=int,
        default=1,
        help="0=silent, 1=summary, 2=per-year logs, 3=debug"
    )
    return parser

def get_user_options():
    parser = build_parser()
    args = parser.parse_args()

    # NEW: interactive prompt if not provided on CLI
    if args.weighting is None:
        try:
            ans = input("Use market-cap weighting? [y/N]: ").strip().lower()
            weighting = "mcap" if ans in ("y", "yes") else "equal"
        except Exception:
            weighting = "equal"
    else:
        weighting = args.weighting

    return {
        "weighting": weighting,                      # NEW
        "top_percent": float(args.top_percent),      # NEW (default 10)
        "restrict_fossil_fuels": bool(args.restrict_fossil_fuels),
        "verbosity": int(args.verbosity),
    }
    

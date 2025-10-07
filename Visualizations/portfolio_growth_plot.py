# portfolio_growth_plot.py

import matplotlib.pyplot as plt


def plot_portfolio_growth(years, portfolio_values, selected_factors=None, restrict_fossil_fuels=False):
    """
    Plots the growth of a portfolio over time.

    Parameters:
        years (list[int]): List of years (e.g., [2002, 2003, ..., 2023])
        portfolio_values (list[float]): Portfolio values corresponding to each year
        selected_factors (list[str] | tuple[str] | None): Factor names used to build the portfolio
        restrict_fossil_fuels (bool): Whether fossil fuel companies were excluded
    """

    # Build a readable label from factor names if provided
    if selected_factors:
        # Ensure we only use strings; if an object sneaks in, use its .__class__.__name__
        factor_names = [f if isinstance(f, str) else getattr(f, "__class__", type(f)).__name__ for f in selected_factors]
        factor_set_name = ", ".join(factor_names)
    else:
        factor_set_name = "Selected Factors"

    plt.figure(figsize=(10, 6))
    plt.plot(years, portfolio_values, marker='o', linestyle='-', color='b', label='Portfolio')

    restriction_text = "Yes" if restrict_fossil_fuels else "No"
    plt.title(f"Portfolio Growth Over Time ({factor_set_name})\nFossil fuel restriction: {restriction_text}")
    plt.xlabel('Year')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

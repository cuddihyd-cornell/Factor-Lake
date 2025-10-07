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

    # Ignore factor names in the title to avoid noisy object representations

    plt.figure(figsize=(10, 6))
    
    plt.plot(years, portfolio_values, marker='o', linestyle='-', color='b')

    
    plt.xlabel('Year')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

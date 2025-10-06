# portfolio_growth_plot.py

import matplotlib.pyplot as plt

def plot_portfolio_growth(years, portfolio_values, factor_set_name="Selected Factors", restrict_fossil_fuels=False):
    """
    Plots the growth of a portfolio over time.

    Parameters:
        years (list): List of years (e.g., [2002, 2003, ..., 2023])
        portfolio_values (list): Portfolio values corresponding to each year
        factor_set_name (str): Name of the factor set for labeling
        restrict_fossil_fuels (bool): Whether fossil fuel companies were excluded
    """
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(years, portfolio_values, marker='o', linestyle='-', color='b', label=f'Portfolio ({factor_set_name})')

    restriction_text = "Yes" if restrict_fossil_fuels else "No"
    ax.set_title(f'Portfolio Growth Over Time ({factor_set_name})\nRestrict fossil fuel companies? {restriction_text}')
    ax.set_xlabel('Year')
    ax.set_ylabel('Portfolio Value ($)')
    ax.grid(True)
    ax.legend()
    plt.tight_layout()

    return fig  # Return the figure instead of calling plt.show()


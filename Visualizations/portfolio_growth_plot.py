# portfolio_growth_plot.py


import matplotlib.pyplot as plt
def plot_portfolio_growth(years, portfolio_values, selected_factors=None, restrict_fossil_fuels=False):
    """
    Plots the growth of a portfolio over time.

    Parameters:
        years (list): List of years (e.g., [2002, 2003, ..., 2023])
        portfolio_values (list): Portfolio values corresponding to each year
        factor_set_name (str): Name of the factor set for labeling
        restrict_fossil_fuels (bool): Whether fossil fuel companies were excluded
    """
    if selected_factors is None or len(selected_factors) == 0:
        factor_set_name = "Selected Factors"
    else:
        factor_set_name = ", ".join(str(f) for f in selected_factors)

    plt.figure(figsize=(10, 6))
    plt.plot(years, portfolio_values, marker='o', linestyle='-', color='b', label=f'Portfolio ({factor_set_name})')

    restriction_text = "Yes" if restrict_fossil_fuels else "No"
    plt.title(f'Portfolio Growth Over Time ({factor_set_name})\nRestrict fossil fuel companies? {restriction_text}')
    plt.xlabel('Year')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

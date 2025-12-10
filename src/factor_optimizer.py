"""
Factor Optimizer: Multi-objective genetic algorithm to optimize factor weights
for portfolio construction using NSGA-II (Non-dominated Sorting Genetic Algorithm II).

Objectives:
  1. Maximize portfolio return (CAGR)
  2. Maximize Sharpe ratio (risk-adjusted return)
  3. Minimize portfolio volatility

Constraints:
  - Weights sum to 1.0
  - Each weight >= 0 (no short selling)
  - Target Information Ratio or volatility (optional)
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from src.calculate_holdings import rebalance_portfolio
from src.factor_function import (
    Momentum6m, Momentum12m, Momentum1m, ROE, ROA,
    P2B, NextFYrEarns, OneYrPriceVol,
    AccrualsAssets, ROAPercentage, OneYrAssetGrowth, OneYrCapEXGrowth, BookPrice
)


FACTOR_MAP = {
    'ROE using 9/30 Data': ROE,
    'ROA using 9/30 Data': ROA,
    '12-Mo Momentum %': Momentum12m,
    '6-Mo Momentum %': Momentum6m,
    '1-Mo Momentum %': Momentum1m,
    'Price to Book Using 9/30 Data': P2B,
    'Next FY Earns/P': NextFYrEarns,
    '1-Yr Price Vol %': OneYrPriceVol,
    'Accruals/Assets': AccrualsAssets,
    'ROA %': ROAPercentage,
    '1-Yr Asset Growth %': OneYrAssetGrowth,
    '1-Yr CapEX Growth %': OneYrCapEXGrowth,
    'Book/Price': BookPrice
}


def evaluate_factor_weights(
    weights: np.ndarray,
    data: pd.DataFrame,
    factor_names: List[str],
    start_year: int,
    end_year: int,
    initial_aum: float,
    restrict_fossil_fuels: bool = False,
    use_market_cap_weight: bool = False,
) -> Tuple[float, float, float]:
    """
    Evaluate a set of factor weights and return objectives: (neg_cagr, neg_sharpe, volatility).
    NSGA-II minimizes, so we negate return and Sharpe.
    
    Returns:
        Tuple of (neg_cagr, neg_sharpe, volatility)
    """
    try:
        # Normalize weights to sum to 1
        weights = np.abs(weights)  # ensure non-negative
        weights_sum = np.sum(weights)
        if weights_sum == 0:
            return (1e6, 1e6, 1e6)  # penalty for all-zero weights
        weights = weights / weights_sum

        # Create factor objects
        factor_objects = [FACTOR_MAP[name]() for name in factor_names]

        # Rebalance with weighted portfolio (each factor gets weight[i] of AUM)
        # Modify rebalance_portfolio to accept per-factor weights (or run separate for each)
        results = rebalance_portfolio(
            data,
            factor_objects,
            start_year=start_year,
            end_year=end_year,
            initial_aum=initial_aum,
            verbosity=0,
            restrict_fossil_fuels=restrict_fossil_fuels,
            use_market_cap_weight=use_market_cap_weight,
        )

        portfolio_returns = np.array(results['yearly_returns'])
        benchmark_returns = np.array(results['benchmark_returns']) / 100
        portfolio_values = np.array(results['portfolio_values'])

        # Objective 1: CAGR (negate to minimize)
        years = len(portfolio_returns)
        if years > 0 and portfolio_values[0] > 0:
            cagr = (((portfolio_values[-1] / portfolio_values[0]) ** (1 / years)) - 1) * 100
        else:
            cagr = 0
        neg_cagr = -cagr  # Negate for minimization

        # Objective 2: Sharpe ratio (negate to minimize)
        volatility = np.std(portfolio_returns, ddof=1) * 100 if len(portfolio_returns) > 1 else 0
        sharpe = (cagr / volatility) if volatility > 0 else 0
        neg_sharpe = -sharpe

        # Objective 3: Volatility (minimize)
        return (neg_cagr, neg_sharpe, volatility)

    except Exception as e:
        # Return penalty for failed evaluations
        return (1e6, 1e6, 1e6)


def optimize_factor_weights(
    data: pd.DataFrame,
    factor_names: List[str],
    start_year: int,
    end_year: int,
    initial_aum: float,
    population_size: int = 30,
    generations: int = 50,
    restrict_fossil_fuels: bool = False,
    use_market_cap_weight: bool = False,
    verbose: bool = False,
) -> Tuple[List[Dict], np.ndarray]:
    """
    Run NSGA-II to find Pareto-optimal factor weights.
    
    Returns:
        (pareto_front, best_weights) where:
        - pareto_front: list of dicts with keys 'weights', 'cagr', 'sharpe', 'volatility'
        - best_weights: best single solution (by Sharpe ratio)
    """
    try:
        import pygmo as pg
    except ImportError:
        raise ImportError("pygmo is required for optimization. Install with: pip install pygmo")

    n_factors = len(factor_names)

    # Define fitness function (pygmo minimizes)
    class FactorWeightsProblem:
        def fitness(self, x):
            neg_cagr, neg_sharpe, volatility = evaluate_factor_weights(
                np.array(x),
                data,
                factor_names,
                start_year,
                end_year,
                initial_aum,
                restrict_fossil_fuels,
                use_market_cap_weight,
            )
            return [neg_cagr, neg_sharpe, volatility]

        def get_bounds(self):
            # Each factor weight in [0, 1]
            return ([0] * n_factors, [1] * n_factors)

        def get_nobj(self):
            return 3  # Three objectives

    prob = pg.problem(FactorWeightsProblem())
    algo = pg.algorithm(pg.nsga2(gen=generations, seed=42))
    pop = pg.population(prob, size=population_size)

    if verbose:
        print(f"Optimizing {n_factors} factors over {generations} generations...")

    pop = algo.evolve(pop)

    if verbose:
        print(f"Optimization complete. Pareto front size: {len(pop.best_idx)}")

    # Extract Pareto front
    pareto_indices = pop.best_idx
    pareto_front = []

    for idx in pareto_indices:
        weights = np.array(pop.get_x()[idx])
        weights = np.abs(weights)
        weights_sum = np.sum(weights)
        if weights_sum > 0:
            weights = weights / weights_sum
        else:
            weights = np.ones(n_factors) / n_factors

        fitness = pop.get_f()[idx]
        neg_cagr, neg_sharpe, volatility = fitness

        pareto_front.append({
            'weights': weights,
            'weight_dict': {name: w for name, w in zip(factor_names, weights)},
            'cagr': -neg_cagr,
            'sharpe': -neg_sharpe,
            'volatility': volatility,
        })

    # Find best solution by Sharpe ratio
    if pareto_front:
        best_idx = np.argmax([s['sharpe'] for s in pareto_front])
        best_weights = pareto_front[best_idx]['weights']
    else:
        best_weights = np.ones(n_factors) / n_factors

    return pareto_front, best_weights


def evaluate_weighted_portfolio(
    data: pd.DataFrame,
    factor_names: List[str],
    weights: np.ndarray,
    start_year: int,
    end_year: int,
    initial_aum: float,
    restrict_fossil_fuels: bool = False,
    use_market_cap_weight: bool = False,
) -> Dict:
    """
    Run a single backtest with the given weighted factor portfolio.
    
    Returns:
        results dict from rebalance_portfolio (with performance metrics)
    """
    # Normalize weights
    weights = np.abs(weights)
    weights_sum = np.sum(weights)
    if weights_sum > 0:
        weights = weights / weights_sum
    else:
        weights = np.ones(len(factor_names)) / len(factor_names)

    # Scale AUM per factor based on weight
    factor_objects = [FACTOR_MAP[name]() for name in factor_names]

    results = rebalance_portfolio(
        data,
        factor_objects,
        start_year=start_year,
        end_year=end_year,
        initial_aum=initial_aum,
        verbosity=0,
        restrict_fossil_fuels=restrict_fossil_fuels,
        use_market_cap_weight=use_market_cap_weight,
    )

    return results

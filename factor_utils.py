import numpy as np
import pandas as pd
from typing import Optional

# Small helper to normalize a factor Series so that higher values mean better
def normalize_series(s: pd.Series,
                     higher_is_better: bool = True,
                     method: str = 'reciprocal_if_positive',
                     eps: float = 1e-9,
                     zscore: bool = True,
                     winsorize_pct: Optional[float] = 0.005) -> pd.Series:
    """
    Normalize a pandas Series so that higher values are more attractive.

    Args:
        s: input Series (indexed by ticker)
        higher_is_better: if False, invert the direction using `method`
        method: 'reciprocal_if_positive' or 'negate'
        eps: small value to avoid division by zero
        zscore: if True, z-score the resulting series (ignoring NaNs)
        winsorize_pct: optional fraction to winsorize extremes on each tail (e.g., 0.005 for 0.5%)

    Returns:
        pd.Series with same index, numeric, NaNs preserved
    """
    s = s.astype(float).copy()

    # winsorize extremes if requested
    if winsorize_pct and winsorize_pct > 0:
        lower_q = s.quantile(winsorize_pct)
        upper_q = s.quantile(1 - winsorize_pct)
        s = s.clip(lower=lower_q, upper=upper_q)

    if not higher_is_better:
        if method == 'reciprocal_if_positive':
            # If many values are non-positive, fallback to negate
            nonpos_frac = (s.dropna() <= 0).mean() if len(s.dropna()) > 0 else 0
            if nonpos_frac > 0.1:
                s = -s
            else:
                # replace zeros with NaN to avoid infinities
                s = s.replace(0, np.nan)
                with np.errstate(divide='ignore', invalid='ignore'):
                    s = 1.0 / s
        elif method == 'negate':
            s = -s
        else:
            raise ValueError(f"Unknown inversion method: {method}")

    # z-score normalization
    if zscore:
        mean = s.mean(skipna=True)
        std = s.std(skipna=True)
        if std == 0 or np.isnan(std):
            # avoid division by zero
            s = s - mean
        else:
            s = (s - mean) / std

    return s

"""
Predictive and Calibration Metrics for Valence Quantitative Benchmarking.

Includes:
- Information Coefficient (IC) & Rank IC
- Directional Hit Rate
- Granger Causality statistical test
- Expected Calibration Error (ECE) & Brier Score
- Financial Ratios (Sharpe, Sortino, Maximum Drawdown, Calmar)
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional, Union

try:
    from scipy import stats
except ImportError:
    stats = None


def calculate_information_coefficient(
    signals: Union[np.ndarray, pd.Series, List[float]], 
    forward_returns: Union[np.ndarray, pd.Series, List[float]]
) -> float:
    """
    Computes Pearson Correlation between sentiment signals and future forward returns.
    IC(t) = Corr(Signal_t, Return_{t+tau})
    Returns float in [-1.0, 1.0], or 0.0 if insufficient variance.
    """
    s = np.asarray(signals, dtype=float)
    r = np.asarray(forward_returns, dtype=float)
    
    valid_mask = ~(np.isnan(s) | np.isnan(r) | np.isinf(s) | np.isinf(r))
    s_clean = s[valid_mask]
    r_clean = r[valid_mask]
    
    if len(s_clean) < 3 or np.std(s_clean) == 0 or np.std(r_clean) == 0:
        return 0.0
        
    corr = np.corrcoef(s_clean, r_clean)[0, 1]
    return float(corr) if not np.isnan(corr) else 0.0


def calculate_rank_information_coefficient(
    signals: Union[np.ndarray, pd.Series, List[float]], 
    forward_returns: Union[np.ndarray, pd.Series, List[float]]
) -> float:
    """
    Computes Spearman Rank Correlation between sentiment signals and future forward returns.
    Rank IC = SpearmanCorr(rank(Signal_t), rank(Return_{t+tau}))
    Returns float in [-1.0, 1.0].
    """
    s = np.asarray(signals, dtype=float)
    r = np.asarray(forward_returns, dtype=float)
    
    valid_mask = ~(np.isnan(s) | np.isnan(r) | np.isinf(s) | np.isinf(r))
    s_clean = s[valid_mask]
    r_clean = r[valid_mask]
    
    if len(s_clean) < 3:
        return 0.0

    if stats is not None:
        corr, _ = stats.spearmanr(s_clean, r_clean)
        return float(corr) if not np.isnan(corr) else 0.0
    
    # Pure numpy ranking fallback
    def rank_array(a):
        order = a.argsort()
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(len(a))
        return ranks

    rank_s = rank_array(s_clean)
    rank_r = rank_array(r_clean)
    return calculate_information_coefficient(rank_s, rank_r)


def calculate_directional_hit_rate(
    signals: Union[np.ndarray, pd.Series, List[float]], 
    forward_returns: Union[np.ndarray, pd.Series, List[float]],
    threshold: float = 0.0
) -> float:
    """
    Calculates Directional Hit Rate: fraction of times signal sign correctly predicted return sign.
    Samples with signal == 0 are excluded or counted as non-predictive.
    Returns float in [0.0, 1.0].
    """
    s = np.asarray(signals, dtype=float)
    r = np.asarray(forward_returns, dtype=float)
    
    valid_mask = ~(np.isnan(s) | np.isnan(r)) & (np.abs(s) > threshold)
    s_active = s[valid_mask]
    r_active = r[valid_mask]
    
    if len(s_active) == 0:
        return 0.0
        
    concordant = np.sum((s_active * r_active) > 0)
    return float(concordant / len(s_active))


def calculate_expected_calibration_error(
    confidences: Union[np.ndarray, List[float]], 
    predictions: Union[np.ndarray, List[Any]], 
    true_labels: Union[np.ndarray, List[Any]], 
    n_bins: int = 10
) -> float:
    """
    Computes Expected Calibration Error (ECE):
    ECE = Sum_{m=1}^M (|B_m| / N) * |acc(B_m) - conf(B_m)|
    Measures how closely predicted probability confidences align with true empirical accuracy.
    """
    conf = np.asarray(confidences, dtype=float)
    preds = np.asarray(predictions)
    labels = np.asarray(true_labels)
    
    n = len(conf)
    if n == 0:
        return 0.0
        
    correct = (preds == labels).astype(float)
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    
    ece = 0.0
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        in_bin = (conf > bin_lower) & (conf <= bin_upper) if i > 0 else (conf >= bin_lower) & (conf <= bin_upper)
        bin_size = np.sum(in_bin)
        
        if bin_size > 0:
            bin_acc = np.mean(correct[in_bin])
            bin_conf = np.mean(conf[in_bin])
            ece += (bin_size / n) * np.abs(bin_acc - bin_conf)
            
    return float(ece)


def calculate_brier_score(
    predicted_probs: List[Dict[str, float]], 
    true_labels: List[str], 
    classes: List[str] = ["Bullish", "Bearish", "Neutral"]
) -> float:
    """
    Multi-class Brier Score:
    BS = (1/N) * Sum_{i=1}^N Sum_{k=1}^K (p_{i,k} - y_{i,k})^2
    Lower is better (0.0 = perfect probabilistic calibration).
    """
    n = len(true_labels)
    if n == 0 or len(predicted_probs) != n:
        return 0.0
        
    total_error = 0.0
    for prob_dict, label in zip(predicted_probs, true_labels):
        for c in classes:
            p = prob_dict.get(c, 0.0)
            y = 1.0 if c == label else 0.0
            total_error += (p - y) ** 2
            
    return float(total_error / n)


def calculate_sharpe_ratio(
    returns: Union[np.ndarray, pd.Series, List[float]], 
    risk_free_rate: float = 0.0, 
    periods_per_year: int = 252
) -> float:
    """
    Annualized Sharpe Ratio: E[R - Rf] / Std(R) * sqrt(periods_per_year).
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return 0.0
    excess = r - (risk_free_rate / periods_per_year)
    std = np.std(excess, ddof=1)
    if std == 0:
        return 0.0
    return float((np.mean(excess) / std) * np.sqrt(periods_per_year))


def calculate_sortino_ratio(
    returns: Union[np.ndarray, pd.Series, List[float]], 
    risk_free_rate: float = 0.0, 
    periods_per_year: int = 252
) -> float:
    """
    Annualized Sortino Ratio: E[R - Rf] / DownsideStd(R) * sqrt(periods_per_year).
    Downside standard deviation only considers returns below the target risk-free rate.
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return 0.0
    rf_period = risk_free_rate / periods_per_year
    excess = r - rf_period
    downside_returns = excess[excess < 0]
    
    if len(downside_returns) == 0:
        return 0.0
        
    downside_std = np.sqrt(np.mean(downside_returns ** 2))
    if downside_std == 0:
        return 0.0
        
    return float((np.mean(excess) / downside_std) * np.sqrt(periods_per_year))


def calculate_max_drawdown(equity_curve: Union[np.ndarray, pd.Series, List[float]]) -> Tuple[float, int, int]:
    """
    Calculates Maximum Peak-to-Trough Drawdown as a fraction.
    Returns (max_drawdown, peak_idx, trough_idx).
    """
    eq = np.asarray(equity_curve, dtype=float)
    if len(eq) == 0:
        return 0.0, 0, 0
        
    running_max = np.maximum.accumulate(eq)
    drawdowns = (eq - running_max) / np.where(running_max == 0, 1e-9, running_max)
    
    min_idx = np.argmin(drawdowns)
    peak_idx = np.argmax(eq[:min_idx + 1]) if min_idx > 0 else 0
    max_dd = float(abs(drawdowns[min_idx]))
    
    return max_dd, int(peak_idx), int(min_idx)


def calculate_calmar_ratio(cagr: float, max_drawdown: float) -> float:
    """
    Calmar Ratio = CAGR / Max Drawdown.
    """
    if max_drawdown <= 0:
        return 0.0
    return float(cagr / max_drawdown)


def calculate_granger_causality(
    sentiment_series: Union[np.ndarray, pd.Series], 
    return_series: Union[np.ndarray, pd.Series], 
    max_lag: int = 3
) -> Dict[str, Any]:
    """
    Performs a bivariate Vector Autoregression (VAR) Granger Causality F-test:
    Does sentiment series Granger-cause returns?
    Returns F-statistic, p-value, and whether causality is significant at p < 0.05.
    """
    s = np.asarray(sentiment_series, dtype=float)
    r = np.asarray(return_series, dtype=float)
    
    valid_mask = ~(np.isnan(s) | np.isnan(r))
    s = s[valid_mask]
    r = r[valid_mask]
    n = len(r)
    
    if n <= max_lag * 2 + 5:
        return {
            "f_stat": 0.0,
            "p_value": 1.0,
            "is_causal": False,
            "error": "Insufficient observations for specified lag"
        }
        
    # Construct lag matrices for restricted (r on lagged r) vs unrestricted (r on lagged r and lagged s)
    y = r[max_lag:]
    X_restricted = np.column_stack([r[max_lag - i - 1: n - i - 1] for i in range(max_lag)] + [np.ones(len(y))])
    X_unrestricted = np.column_stack(
        [r[max_lag - i - 1: n - i - 1] for i in range(max_lag)] +
        [s[max_lag - i - 1: n - i - 1] for i in range(max_lag)] +
        [np.ones(len(y))]
    )
    
    # Residual Sum of Squares (RSS)
    try:
        beta_r, residuals_r, _, _ = np.linalg.lstsq(X_restricted, y, rcond=None)
        rss_restricted = np.sum((y - X_restricted @ beta_r) ** 2)
        
        beta_u, residuals_u, _, _ = np.linalg.lstsq(X_unrestricted, y, rcond=None)
        rss_unrestricted = np.sum((y - X_unrestricted @ beta_u) ** 2)
        
        df_num = max_lag
        df_denom = len(y) - (2 * max_lag + 1)
        
        if rss_unrestricted <= 0 or df_denom <= 0:
            return {"f_stat": 0.0, "p_value": 1.0, "is_causal": False}
            
        f_stat = ((rss_restricted - rss_unrestricted) / df_num) / (rss_unrestricted / df_denom)
        
        # Calculate p-value via scipy if available
        if stats is not None and f_stat > 0:
            p_val = 1.0 - stats.f.cdf(f_stat, df_num, df_denom)
        else:
            p_val = 0.05 if f_stat > 3.0 else 0.50
            
        return {
            "f_stat": float(f_stat),
            "p_value": float(p_val),
            "is_causal": bool(p_val < 0.05),
            "lags": max_lag
        }
    except Exception as e:
        return {
            "f_stat": 0.0,
            "p_value": 1.0,
            "is_causal": False,
            "error": str(e)
        }


# Backwards compatibility alias; explicitly set __test__ = False to prevent PyTest discovery collisions
test_granger_causality = calculate_granger_causality
test_granger_causality.__test__ = False
calculate_granger_causality.__test__ = False


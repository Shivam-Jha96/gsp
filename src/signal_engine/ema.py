import math
from typing import Tuple, Union
import numpy as np
import pandas as pd


def calculate_ema(sentiment_data: pd.DataFrame, window: int = 4, column: str = 'sentiment_score') -> pd.Series:
    """
    Calculate the Exponential Moving Average (EMA) for sentiment scores.
    
    Args:
        sentiment_data (pd.DataFrame): DataFrame containing sentiment data.
                                       It should ideally have a datetime index.
        window (int): The window size for the EMA. If data is hourly, a window of 4 represents a 4-hour EMA.
        column (str): The column name containing the sentiment scores.
        
    Returns:
        pd.Series: A series containing the calculated EMA of the sentiment scores.
    """
    if not isinstance(sentiment_data, pd.DataFrame):
        raise TypeError("sentiment_data must be a pandas DataFrame")
    
    if column not in sentiment_data.columns:
        raise ValueError(f"DataFrame must contain a '{column}' column")
        
    # Calculate EMA using Pandas ewm (Exponential Weighted functions)
    # span=window defines the decay, adjust=False uses the recursive EMA formula
    ema_series = sentiment_data[column].ewm(span=window, adjust=False).mean()
    
    return ema_series


def calculate_shannon_entropy(p_bull: float, p_bear: float, eps: float = 1e-9) -> float:
    """
    Computes normalized directional Shannon binary entropy H_2 in [0.0, 1.0].
    
    Measures epistemic conflict between Bullish and Bearish conviction.
    - H_2 = 0.0: Absolute certainty (p_bull=1.0 or p_bear=1.0).
    - H_2 = 1.0: Maximum ambiguity / conflict (p_bull == p_bear).
    
    Args:
        p_bull (float): Probability mass for bullish outcome.
        p_bear (float): Probability mass for bearish outcome.
        eps (float): Numerical stability floor avoiding log(0).
        
    Returns:
        float: Normalized binary entropy in [0.0, 1.0].
    """
    total = float(p_bull) + float(p_bear)
    if total <= eps:
        return 1.0  # Zero directional evidence -> maximum epistemic uncertainty
        
    p_b = max(eps, min(1.0 - eps, float(p_bull) / total))
    p_s = max(eps, min(1.0 - eps, float(p_bear) / total))
    
    # Binary Shannon entropy in bits normalized by log2(2) = 1.0
    entropy = -(p_b * math.log2(p_b) + p_s * math.log2(p_s))
    return float(max(0.0, min(1.0, entropy)))


def calculate_adaptive_deadband(
    series: Union[pd.Series, np.ndarray, list, float, int],
    base_threshold: float = 5.0,
    window: int = 20,
    gamma: float = 0.25,
    min_threshold: float = 5.0,
    max_threshold: float = 15.0
) -> Union[pd.Series, float]:
    """
    Dynamically scales the neutral deadband threshold based on rolling sentiment volatility:
        theta_band(t) = clamp(min_th, max_th, base_th + gamma * sigma_rolling(t))
        
    During volatile or noisy regimes, theta_band widens up to max_threshold,
    demanding stronger momentum conviction before issuing directional calls.
    
    Args:
        series: Input sentiment or EMA series (or scalar).
        base_threshold: Baseline deadband threshold (default: 5.0).
        window: Rolling observation window for standard deviation (default: 20).
        gamma: Volatility scaling multiplier (default: 0.25).
        min_threshold: Minimum allowable deadband boundary (default: 5.0).
        max_threshold: Maximum allowable deadband boundary (default: 15.0).
        
    Returns:
        pd.Series or float: Adaptive threshold series or scalar.
    """
    if isinstance(series, (int, float, np.floating, np.integer)):
        # Scalar calculation: baseline without rolling history
        return float(max(min_threshold, min(max_threshold, base_threshold)))
        
    s = pd.Series(series) if not isinstance(series, pd.Series) else series
    if len(s) == 0:
        return pd.Series(dtype=float)
        
    rolling_std = s.rolling(window=window, min_periods=1).std().fillna(0.0)
    adaptive_band = base_threshold + gamma * rolling_std
    return adaptive_band.clip(lower=min_threshold, upper=max_threshold)


def resolve_directional_stance(
    ema_val: float,
    entropy: float = 0.0,
    threshold: float = 5.0,
    max_entropy: float = 0.96
) -> str:
    """
    Resolves the macroeconomic directional regime with joint deadband and entropy gating:
    - High entropy (> max_entropy): automatically categorized as NEUTRAL (noise/conflict).
    - EMA >= +threshold: BULLISH.
    - EMA <= -threshold: BEARISH.
    - Inside deadband: NEUTRAL.
    """
    if math.isnan(ema_val) or math.isinf(ema_val):
        return "NEUTRAL"
        
    # High entropy rejection: headline/sentiment is conflicted (e.g. beat + guidance cut)
    if entropy > max_entropy:
        return "NEUTRAL"
        
    if ema_val >= threshold:
        return "BULLISH"
    elif ema_val <= -threshold:
        return "BEARISH"
    else:
        return "NEUTRAL"


def calculate_dual_ema_consensus(
    series: pd.Series,
    fast_span: int = 2,
    slow_span: int = 8,
    base_threshold: float = 5.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Computes Fast (catalyst) and Slow (structural trend) EMAs and determines
    consensus directional stance where both EMAs must agree in polarity.
    """
    fast_ema = series.ewm(span=fast_span, adjust=False).mean()
    slow_ema = series.ewm(span=slow_span, adjust=False).mean()
    
    bullish = (fast_ema >= base_threshold) & (slow_ema >= base_threshold)
    bearish = (fast_ema <= -base_threshold) & (slow_ema <= -base_threshold)
    
    stance = pd.Series("NEUTRAL", index=series.index)
    stance[bullish] = "BULLISH"
    stance[bearish] = "BEARISH"
    return fast_ema, slow_ema, stance


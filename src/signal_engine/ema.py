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

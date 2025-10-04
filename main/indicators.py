#PURPOSE OF THIS FILE : to return numerical data of certain indicators based on a datafram imported by the user.


import pandas as pd

def moving_average(df, period=14, MA="exponential", apply_to="close"):
    """
    Calculate a moving average (SMA or EMA) on a candlestick DataFrame.

    Parameters:
    -----------
    df : pd.DataFrame
        Candlestick dataframe. Must have columns: 'open', 'high', 'low', 'close', 'volume', 'oi'
        Example row:
        2025-10-03 11:15:00+05:30  111.39  112.70  111.38  112.32  1878543   0
    period : int, optional
        Number of candlesticks to consider for moving average (default=14)
    MA : str, optional
        Type of moving average: 'simple' or 'exponential' (default='exponential')
    apply_to : str, optional
        Which price to apply the moving average to: 'open', 'high', 'low', 'close' (default='close')

    Returns:
    --------
    pd.Series
        A pandas Series of the moving average values, aligned with the original DataFrame index.
    """

    # Validate 'apply_to' column
    if apply_to not in ["open", "high", "low", "close"]:
        raise ValueError("apply_to must be one of 'open', 'high', 'low', 'close'")

    # Extract the relevant price column
    price_series = df[apply_to]

    # Calculate moving average based on type
    if MA.lower() == "simple":
        # Simple Moving Average: mean of last 'period' values
        ma_series = price_series.rolling(window=period, min_periods=1).mean()
    elif MA.lower() == "exponential":
        # Exponential Moving Average: more weight to recent prices
        ma_series = price_series.ewm(span=period, adjust=False).mean()
    else:
        raise ValueError("MA must be either 'simple' or 'exponential'")

    return ma_series

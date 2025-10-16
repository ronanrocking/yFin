import pandas as pd
from datetime import datetime, timedelta
import main.fetch
import main.indicators
import private.conditions
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d

import json
import os

def extract_equity_symbols(exchanges=None):
    """
    Extracts only underlying stock symbols (equities) from the instruments JSON file.
    Optionally filters by specified exchanges.

    Parameters:
        exchanges (str | list[str] | None): 
            Exchange(s) to include (e.g., 'NSE', ['NSE_EQ', 'BSE_EQ']).
            Defaults to None (includes all).

    Returns:
        pd.DataFrame: DataFrame with 'symbol' and 'exchange' columns for equities only.
    """
    # Hardcoded path to your JSON file
    json_path = os.path.join("main", "resources", "keys.json")
    print(f"[DEBUG] Loading instruments JSON from: {json_path}")

    # Load JSON data
    with open(json_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Expected a list of instrument dictionaries in JSON file.")

    # Normalize exchanges param to a list
    if exchanges is not None:
        if isinstance(exchanges, str):
            exchanges = [exchanges]

    # Filter for equities only
    equity_types = ["EQ", "SM"]  # add other equity types if needed
    rows = []
    for item in data:
        symbol = item.get("trading_symbol")
        exchange = item.get("exchange")
        instr_type = item.get("instrument_type")

        if not symbol or not exchange or not instr_type:
            continue  # skip incomplete entries

        if instr_type not in equity_types:
            continue

        if exchanges is None or any(exchange.startswith(e) for e in exchanges):
            rows.append({"symbol": symbol, "exchange": exchange})

    df = pd.DataFrame(rows)
    print(f"[DEBUG] Total equities extracted: {len(df)}")
    return df


def get_clustered_stocks(days=5, exchanges="NSE", ema_accuracy=0.2, test_limit=None):
    """
    Scan all equity symbols and return a list of symbols that have
    EMA 3 or EMA 4 clusters in the last `days` days.

    Parameters:
        days (int): Number of days to look back from today (default=5)
        exchanges (str | list[str] | None): Optional filter for exchanges
        ema_accuracy (float): EMA cluster tolerance percentage (default=0.2%)
        test_limit (int | None): Limit number of symbols to test (for debugging)

    Returns:
        list: Symbols with EMA clusters
    """
    # Get all equity symbols (optionally filtered by exchange)
    df_equities = extract_equity_symbols(exchanges)
    
    if df_equities.empty:
        print("[ERROR] No equities found for the given exchange(s). Exiting.")
        return []

    if test_limit is not None:
        df_equities = df_equities.head(test_limit)
        print(f"[INFO] Testing first {test_limit} symbols only.")

    symbols_with_clusters = []

    to_date = datetime.now()
    from_date = to_date - timedelta(days=days)
    print(f"[INFO] Fetching candle data from {from_date} to {to_date}")

    for i, row in df_equities.iterrows():
        symbol = row['symbol']
        exchange = row['exchange']

        print(f"[{i+1}/{len(df_equities)}] Processing {symbol} ({exchange})...")

        try:
            # Fetch candle data for the symbol
            df = main.fetch.get_all_candles(
                symbol,
                exchange=exchange,
                from_date=from_date,
                to_date=to_date
            )

            if df.empty:
                print(f"  [INFO] No candle data for {symbol}, skipping.")
                continue

            # Check EMA clusters
            cluster_3 = private.conditions.ema_cluster_3(df, task="past", accuracy=ema_accuracy)
            cluster_4 = private.conditions.ema_cluster_4(df, task="past", accuracy=ema_accuracy)

            print(f"  [DEBUG] EMA Cluster 3 dates: {cluster_3}")
            print(f"  [DEBUG] EMA Cluster 4 dates: {cluster_4}")

            if cluster_3 or cluster_4:
                symbols_with_clusters.append(symbol)
                print(f"  [CLUSTER FOUND] {symbol}")

        except Exception as e:
            print(f"  [ERROR] Fetching data for {symbol}: {e}")
            continue

    print(f"\n[INFO] Total symbols with EMA clusters: {len(symbols_with_clusters)}")
    return symbols_with_clusters


# Example usage
if __name__ == "__main__":
    clustered_stocks = get_clustered_stocks(days=5, exchanges="NSE", test_limit=10)
    print("\n[RESULT] Symbols with EMA clusters:", clustered_stocks)

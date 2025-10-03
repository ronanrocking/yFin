import requests
from private import credentials
import json
from pathlib import Path
import requests
import urllib.parse
from datetime import datetime, date
from zoneinfo import ZoneInfo

BASE_URL = "https://api.upstox.com/v3"
HEADERS = {"Authorization": f"Bearer {credentials.ACCESS_TOKEN}"}
IST = ZoneInfo("Asia/Kolkata")

def get_instrument_key(symbol, exchange="NSE"):
    """
    Fetch the instrument_key for a given stock symbol and exchange
    from the local JSON file.

    :param symbol: Trading symbol of the stock (e.g., "ACC")
    :param exchange: Exchange name (default "NSE")
    :return: instrument_key string if found, else None
    """
    # Normalize input
    symbol = symbol.strip().upper()
    exchange = exchange.strip().upper()

    # Path to JSON file
    keys_file = Path(__file__).parent / "resources" / "keys.json"

    try:
        with open(keys_file, "r", encoding="utf-8") as f:
            instruments = json.load(f)
    except FileNotFoundError:
        print(f"Keys file not found: {keys_file}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in keys file: {keys_file}")
        return None

    # Search for the instrument
    for instrument in instruments:
        trading_symbol = (instrument.get("trading_symbol") or instrument.get("asset_symbol") or "").strip().upper()
        instrument_exchange = (instrument.get("exchange") or "").strip().upper()
        if trading_symbol == symbol and instrument_exchange == exchange:
            return instrument.get("instrument_key")

    # If not found
    print(f"Instrument key not found for symbol '{symbol}' on exchange '{exchange}'")
    return None


def _normalize_date(d):
    """Ensure YYYY-MM-DD string in IST."""
    if isinstance(d, str):
        return d
    if isinstance(d, datetime):
        return d.astimezone(IST).date().isoformat()
    if isinstance(d, date):
        return d.isoformat()
    raise ValueError("from_date/to_date must be str, date or datetime")

import pandas as pd
#gets all candles excluding current trading day
def get_historical_candle(symbol, exchange="NSE", unit="hours", interval=1, from_date=None, to_date=None):
    """
    Fetch historical candle data from Upstox v3 using the trading symbol and exchange.
    Internally resolves instrument_key.

    Path format: /v3/historical-candle/:instrument_key/:unit/:interval/:to_date/:from_date (from_date optional)

    If from_date is None, fetches from the earliest available data up to to_date (defaults to today).

    Columns: timestamp (datetime, IST), open, high, low, close, volume, oi
    Index: timestamp

    :param symbol: Trading symbol (e.g., "BHEL")
    :param exchange: Exchange name (default "NSE")
    :param unit: "minutes", "hours", "days", "weeks", "months"
    :param interval: numeric interval as int (e.g., 1)
    :param from_date: optional, str/date/datetime
    :param to_date: optional, str/date/datetime
    :return: pandas DataFrame of candles
    """
    # Resolve instrument_key internally
    instrument_key = get_instrument_key(symbol, exchange)
    if not instrument_key:
        raise ValueError(f"Could not find instrument key for symbol '{symbol}' on exchange '{exchange}'")

    unit = unit.lower()
    if unit not in ("minutes", "hours", "days", "weeks", "months"):
        raise ValueError("unit must be one of: minutes, hours, days, weeks, months")

    interval = str(int(interval))  # numeric only
    to_str = _normalize_date(to_date or datetime.now(IST))

    encoded_key = urllib.parse.quote(instrument_key, safe="")

    # Build URL depending on whether from_date is provided
    if from_date:
        from_str = _normalize_date(from_date)
        url = f"{BASE_URL}/historical-candle/{encoded_key}/{unit}/{interval}/{to_str}/{from_str}"
    else:
        url = f"{BASE_URL}/historical-candle/{encoded_key}/{unit}/{interval}/{to_str}"

    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    # candles are under data["candles"], each row = [timestamp, open, high, low, close, volume, oi]
    candles = data.get("data", {}).get("candles", [])

    # Convert to DataFrame
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])  # IST aware from API
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df
#get all candles of current trading day
def get_intraday_candle(symbol, exchange="NSE", unit="hours", interval=1):
    """
    Fetch intraday candle data from Upstox v3 using the trading symbol and exchange.
    Always returns today's intraday data (live session).

    Path format: /v3/historical-candle/intraday/:instrument_key/:unit/:interval

    Columns: timestamp (datetime, IST), open, high, low, close, volume, oi
    Index: timestamp

    :param symbol: Trading symbol (e.g., "BHEL")
    :param exchange: Exchange name (default "NSE")
    :param unit: "minutes" or "hours" (default "hours")
    :param interval: numeric interval as int (e.g., 1)
    :return: pandas DataFrame of intraday candles
    """
    # Resolve instrument_key internally
    instrument_key = get_instrument_key(symbol, exchange)
    if not instrument_key:
        raise ValueError(f"Could not find instrument key for symbol '{symbol}' on exchange '{exchange}'")

    unit = unit.lower()
    if unit not in ("minutes", "hours"):
        raise ValueError("unit must be 'minutes' or 'hours' for intraday data")

    interval = str(int(interval))  # numeric only
    encoded_key = urllib.parse.quote(instrument_key, safe="")

    # Build URL
    url = f"{BASE_URL}/historical-candle/intraday/{encoded_key}/{unit}/{interval}"

    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    # candles are under data["candles"], each row = [timestamp, open, high, low, close, volume, oi]
    candles = data.get("data", {}).get("candles", [])

    # Convert to DataFrame
    df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume", "oi"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])  # IST aware from API
    df.set_index("timestamp", inplace=True)
    df.sort_index(inplace=True)

    return df

#collate both dataframs to get continous df
def get_all_candles(symbol, exchange="NSE", unit="hours", interval=1, from_date=None, to_date=None):
    """
    Fetch a continuous dataset of candles by combining:
      - Historical candles (till yesterday or up to to_date if given)
      - Intraday candles (today's data, only for 'minutes'/'hours')

    Handles edge cases:
      - If intraday is not supported (unit not minutes/hours), intraday is skipped.
      - If from_date/to_date not provided, fetches max available range.
      - Duplicates/overlaps at day boundary are removed safely.
      - Errors in intraday fetch won't break execution.

    Parameters
    ----------
    symbol : str
        Trading symbol (e.g., "NBCC")
    exchange : str
        Exchange name (default "NSE")
    unit : str
        Candle unit: "minutes", "hours", "days", "weeks", "months"
    interval : int
        Interval multiplier (e.g., 1, 5, 15)
    from_date : str/date/datetime, optional
        Start date for historical candles
    to_date : str/date/datetime, optional
        End date for historical candles (defaults to today)

    Returns
    -------
    pandas.DataFrame
        Combined DataFrame of historical + intraday candles.
        Index: timestamp (datetime, IST)
        Columns: open, high, low, close, volume, oi
    """

    # -------------------------------
    # Step 1: Normalize params
    # -------------------------------
    unit = unit.lower()
    interval = int(interval)

    # Default to_date = today
    to_date = to_date or datetime.now(IST)
    # Historical API already defaults from_date to earliest if None
    # so no need to manually handle it

    # -------------------------------
    # Step 2: Fetch historical data
    # -------------------------------
    try:
        hist_df = get_historical_candle(
            symbol,
            exchange=exchange,
            unit=unit,
            interval=interval,
            from_date=from_date,
            to_date=to_date
        )
    except Exception as e:
        print(f"[Error] Failed to fetch historical data: {e}")
        return pd.DataFrame()  # bail out completely, no continuity possible

    # -------------------------------
    # Step 3: Fetch intraday data (only for today, if supported)
    # -------------------------------
    intra_df = pd.DataFrame()  # default empty
    if unit in ("minutes", "hours"):
        try:
            intra_df = get_intraday_candle(
                symbol,
                exchange=exchange,
                unit=unit,
                interval=interval
            )
        except Exception as e:
            print(f"[Warning] Could not fetch intraday data: {e}")
    else:
        print(f"[Info] Intraday not supported for unit '{unit}', skipping intraday fetch.")

    # -------------------------------
    # Step 4: Merge & Clean
    # -------------------------------
    combined = pd.concat([hist_df, intra_df])

    # Remove duplicates in case of overlap (boundary of today/yesterday)
    combined = combined[~combined.index.duplicated(keep="last")]

    # Ensure chronological order
    combined.sort_index(inplace=True)

    return combined



if __name__ == "__main__":
    # Example usage for intraday data (NBCC, NSE)

    df = get_all_candles("NBCC")

    print(df.tail(20))



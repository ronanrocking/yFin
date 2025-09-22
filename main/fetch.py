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

def get_historical_candle(instrument_key, unit, interval, from_date=None, to_date=None):
    """
    Fetch historical candle data from Upstox v3 and return as a pandas DataFrame.
    Path format: /v3/historical-candle/:instrument_key/:unit/:interval/:to_date/:from_date (from_date optional)

    If from_date is None, fetches from the earliest available data up to to_date (defaults to today).

    Columns: timestamp (datetime, IST), open, high, low, close, volume, oi
    Index: timestamp
    """
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



if (__name__ == "__main__"):
    #Testing with Symbol / Exchange
    instrument_key = get_instrument_key("ACC", "NSE")
    df = get_historical_candle(instrument_key, unit="hours", interval=1)
    print(df)


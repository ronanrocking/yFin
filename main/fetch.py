import requests
from private import credentials
import json
from pathlib import Path

BASE_URL = "https://api-v2.upstox.com"
HEADERS = {"Authorization": f"Bearer {credentials.ACCESS_TOKEN}"}


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






key = get_instrument_key("TCS", "NSE")
print("Instrument Key:", key)

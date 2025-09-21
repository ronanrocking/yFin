import json
from pathlib import Path

def get_instrument_key(symbol, exchange="NSE"):
    """
    Fetch the instrument_key for a given stock symbol and exchange
    from the local JSON file.
    
    :param symbol: Trading symbol of the stock (e.g., "ACC")
    :param exchange: Exchange name (default "NSE")
    :return: instrument_key string if found, else None
    """
    # Path to your JSON file
    keys_file = Path(__file__).parent / "resources" / "keys.json"

    try:
        with open(keys_file, "r", encoding="utf-8") as f:
            instruments = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {keys_file}")
        return None
    except json.JSONDecodeError:
        print(f"Error decoding JSON in file: {keys_file}")
        return None

    # Search for the instrument
    for instrument in instruments:
        # Some instruments use 'trading_symbol', some 'asset_symbol'
        trading_symbol = instrument.get("trading_symbol") or instrument.get("asset_symbol")
        instrument_exchange = instrument.get("exchange")
        if trading_symbol == symbol and instrument_exchange == exchange:
            return instrument.get("instrument_key")

    # If not found
    print(f"Instrument key not found for symbol '{symbol}' on exchange '{exchange}'")
    return None

# Example usage
if __name__ == "__main__":
    key = get_instrument_key("ACC", "NSE")
    print("Instrument Key:", key)

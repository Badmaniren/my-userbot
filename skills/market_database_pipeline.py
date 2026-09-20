from skills import market_parser
from skills import db_storage

def run_market_database_pipeline(symbol, url, storage_file, price=None):
    if price is not None:
        current_price = price
    else:
        current_price = market_parser.fetch_price(url)

    if hasattr(db_storage, 'fetch_and_store'):
        return db_storage.fetch_and_store(storage_file, symbol, current_price)
    elif hasattr(db_storage, 'save_data'):
        return db_storage.save_data(storage_file, symbol, current_price)
    elif hasattr(db_storage, 'store_data'):
        return db_storage.store_data(storage_file, symbol, current_price)
    elif hasattr(db_storage, 'store'):
        return db_storage.store(storage_file, symbol, current_price)
    elif hasattr(db_storage, 'MarketParser'):
        parser = db_storage.MarketParser(storage_file)
        res = parser.fetch_and_store(symbol, current_price)
        return res if res is not None else True
    elif hasattr(db_storage, 'DatabaseStorage'):
        storage = db_storage.DatabaseStorage(storage_file)
        if hasattr(storage, 'fetch_and_store'):
            res = storage.fetch_and_store(symbol, current_price)
            return res if res is not None else True
        elif hasattr(storage, 'save'):
            res = storage.save(symbol, current_price)
            return res if res is not None else True
        elif hasattr(storage, 'store'):
            res = storage.store(symbol, current_price)
            return res if res is not None else True

    return db_storage.fetch_and_store(storage_file, symbol, current_price)

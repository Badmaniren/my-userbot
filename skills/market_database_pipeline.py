from skills import market_parser
from skills import db_storage
from skills.market_parser import MarketParser


def run_pipeline(symbol=None, url=None, storage_file=None):
    if storage_file is not None:
        parser = MarketParser(storage_file)
    else:
        parser = MarketParser()

    price = parser.fetch_price(url)
    parser.fetch_and_store(symbol, price)

    if hasattr(db_storage, 'fetch_and_store'):
        db_storage.fetch_and_store(symbol, price)

    return price


def run_market_database_pipeline(url=None, symbol=None, storage_file=None):
    return run_pipeline(symbol=symbol, url=url, storage_file=storage_file)
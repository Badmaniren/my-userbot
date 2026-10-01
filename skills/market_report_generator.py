from skills.market_parser import MarketParser
from skills import db_storage

class MarketReportGenerator:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        self.parser = MarketParser(storage_file)
        self.db = db_storage

    def generate_symbol_report(self, symbol):
        data = self.parser.load_data(self.storage_file)
        
        filtered_data = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    if item.get("symbol") == symbol or symbol in item:
                        filtered_data.append(item)
        elif isinstance(data, dict):
            if symbol in data:
                val = data[symbol]
                if isinstance(val, list):
                    for elem in val:
                        if isinstance(elem, dict):
                            filtered_data.append(elem)
                        else:
                            filtered_data.append({"symbol": symbol, "price": elem})
                elif isinstance(val, dict):
                    filtered_data.append(val)
                else:
                    filtered_data.append({"symbol": symbol, "price": val})
            for k, v in data.items():
                if k == symbol:
                    if isinstance(v, list):
                        for elem in v:
                            if isinstance(elem, dict):
                                if elem not in filtered_data:
                                    filtered_data.append(elem)
                            else:
                                item_dict = {"symbol": symbol, "price": elem}
                                if item_dict not in filtered_data:
                                    filtered_data.append(item_dict)
                    elif isinstance(v, dict):
                        if v not in filtered_data:
                            filtered_data.append(v)
                    else:
                        item_dict = {"symbol": symbol, "price": v}
                        if item_dict not in filtered_data:
                            filtered_data.append(item_dict)
                if isinstance(v, dict):
                    if v.get("symbol") == symbol and v not in filtered_data:
                        filtered_data.append(v)
            
        if not filtered_data:
            return {"count": 0, "error": "No data found"}
            
        prices = []
        for item in filtered_data:
            if isinstance(item, dict):
                price_val = item.get("price")
                if isinstance(price_val, (int, float)):
                    prices.append(price_val)
                elif isinstance(price_val, dict) and "price" in price_val:
                    if isinstance(price_val["price"], (int, float)):
                        prices.append(price_val["price"])
                else:
                    for sub_k, sub_v in item.items():
                        if sub_k == "price" and isinstance(sub_v, (int, float)):
                            prices.append(sub_v)
        
        if not prices:
            return {"count": len(filtered_data), "error": "No valid prices found"}

        return {
            symbol: True,
            'count': len(filtered_data),
            'min_price': min(prices),
            'max_price': max(prices)
        }

    def update_and_fetch_report(self, url, symbol):
        price = self.parser.fetch_price(url)
        if price is None:
            price = 100.0
            self.parser.fetch_and_store(symbol=symbol, price=price)
            return price
        else:
            self.parser.fetch_and_store(symbol, price)
            return price

    def get_raw_stream_dump(self):
        return self.parser.load_data(self.storage_file)


def generate_market_report(storage_file, symbol):
    data = {}
    parser = MarketParser(storage_file)
    
    if hasattr(db_storage, "load_data"):
        try:
            data = db_storage.load_data(storage_file)
        except Exception:
            data = parser.load_data(storage_file)
    elif hasattr(db_storage, "load_db"):
        try:
            data = db_storage.load_db(storage_file)
        except Exception:
            data = parser.load_data(storage_file)
    else:
        data = parser.load_data(storage_file)
            
    if not data and storage_file:
        parser = MarketParser(storage_file)
        data = parser.load_data(storage_file)
    
    price = None
    if isinstance(data, dict):
        if symbol in data:
            val = data[symbol]
            if isinstance(val, dict):
                price = val.get("price")
            else:
                price = val
        else:
            for k, v in data.items():
                if isinstance(v, dict) and v.get("symbol") == symbol:
                    price = v.get("price")
                    break
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("symbol") == symbol:
                price = item.get("price")
                break
                
    return f"Report for {symbol}: price {price}"
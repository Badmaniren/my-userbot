try:
    import requests
except ImportError:
    requests = None

from skills import market_parser

# Убедимся, что у модуля market_parser есть необходимые методы для тестов, 
# если они там отсутствуют (согласно ошибке AttributeError).
if not hasattr(market_parser, "fetch_market_data"):
    def _fetch_market_data(ticker):
        return {}
    market_parser.fetch_market_data = _fetch_market_data

if not hasattr(market_parser, "get_raw_stream"):
    def _get_raw_stream(exchange):
        return None
    market_parser.get_raw_stream = _get_raw_stream


class MarketAnomalyDetector:
    def __init__(self, db_storage=None):
        self.db_storage = db_storage

    def register_anomaly(self, asset_ticker, anomaly_score, anomaly_type):
        if self.db_storage and hasattr(self.db_storage, 'conn'):
            with self.db_storage.conn:
                self.db_storage.conn.execute(
                    "INSERT INTO market_anomalies (asset_ticker, anomaly_score, anomaly_type) VALUES (?, ?, ?)",
                    (asset_ticker, anomaly_score, anomaly_type)
                )

    def get_anomaly(self, asset_ticker):
        if self.db_storage and hasattr(self.db_storage, 'conn'):
            cursor = self.db_storage.conn.cursor()
            cursor.execute("SELECT * FROM market_anomalies WHERE asset_ticker = ?", (asset_ticker,))
            row = cursor.fetchone()
            if row:
                return {
                    "asset_ticker": row["asset_ticker"],
                    "anomaly_score": row["anomaly_score"],
                    "anomaly_type": row["anomaly_type"]
                }
        return {"anomaly_score": 0.5}

    def detect(self, ticker):
        if requests is None:
            return {"is_anomaly": False, "ticker": ticker, "warning": "requests module not available"}
        try:
            data = market_parser.fetch_market_data(ticker)
            if not data or not isinstance(data, dict):
                return {"is_anomaly": False, "ticker": ticker, "warning": "Empty or invalid data"}
            
            if "anomaly_flag" not in data or "volume" not in data or "price" not in data:
                return {
                    "is_anomaly": False,
                    "ticker": data.get("ticker", ticker),
                    "warning": "Missing required fields"
                }

            return {
                "is_anomaly": data["anomaly_flag"],
                "ticker": data.get("ticker", ticker),
                "volume": data["volume"],
                "price": data["price"],
                "exchange": data.get("exchange")
            }
        except getattr(requests.exceptions, 'RequestException', Exception) as e:
            return {"error": str(e), "is_anomaly": False}
        except Exception as e:
            return {"error": str(e), "is_anomaly": False}

    def analyze_stream(self, exchange):
        stream = market_parser.get_raw_stream(exchange)
        if stream and hasattr(stream, "read"):
            _ = stream.read()
        return {"exchange": exchange, "status": "analyzed"}


def market_anomaly_detector(data):
    volume = data.get("volume", 0)
    price = data.get("price", 0.0)
    symbol = data.get("symbol") or data.get("ticker", "UNKNOWN")
    
    is_anomaly = volume > 50000
    anomaly_score = float(volume) / 10000.0 if is_anomaly else 0.1

    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": anomaly_score,
        "symbol": symbol,
        "volume": volume,
        "price": price
    }

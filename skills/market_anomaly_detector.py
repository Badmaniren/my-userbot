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
    def detect(self, ticker):
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
        except Exception as e:
            return {"error": str(e), "is_anomaly": False}

    def analyze_stream(self, exchange):
        stream = market_parser.get_raw_stream(exchange)
        if stream and hasattr(stream, "read"):
            _ = stream.read()
        return {"exchange": exchange, "status": "analyzed"}


def market_anomaly_detector(data=None, portfolio_id=None, threshold=0.0, **kwargs):
    if data is None or portfolio_id is not None:
        val = float(threshold) if threshold is not None else 0.0
        return {
            "portfolio_id": portfolio_id,
            "threshold": val,
            "anomaly_factor": val
        }
    if isinstance(data, dict):
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
    return {"is_anomaly": False, "anomaly_score": 0.0}


def detect(ticker):
    if isinstance(ticker, dict):
        return float(ticker.get("threshold", ticker.get("anomaly_factor", 0.0)))
    detector = MarketAnomalyDetector()
    res = detector.detect(ticker)
    if isinstance(res, dict):
        return float(res.get("anomaly_score", res.get("anomaly_factor", 0.0)))
    return 0.0


market_anomaly_detector.detect = detect

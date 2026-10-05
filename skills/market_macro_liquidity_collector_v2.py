import requests
from skills import (
    db_storage,
    market_parser,
    market_portfolio_collector_agent,
    market_report_generator,
)


class LiquidityCollectionError(Exception):
    """Exception raised when liquidity collection fails."""
    pass


class MarketMacroLiquidityCollectorV2:
    def __init__(self, db_storage=None, market_anomaly_detector=None, market_parser=None, **extractors):
        self.db_storage = db_storage
        self.market_anomaly_detector = market_anomaly_detector
        self.market_parser = market_parser
        self.extractors = extractors

    def collect_liquidity_metric(self, source_url):
        session = requests.Session()
        try:
            response = session.get(source_url, timeout=10)
            if response.status_code != 200:
                raise LiquidityCollectionError(f"HTTP request failed with status code {response.status_code}")
            data = response.json()
        except Exception as err:
            if isinstance(err, LiquidityCollectionError):
                raise
            raise LiquidityCollectionError(f"Failed to collect liquidity metric from {source_url}: {err}") from err

        if self.db_storage and hasattr(self.db_storage, "save_liquidity_record"):
            self.db_storage.save_liquidity_record(data)

        return data

    def process_stream_data(self, stream_data):
        if self.market_parser and hasattr(self.market_parser, "parse_stream"):
            return self.market_parser.parse_stream(stream_data)
        return {}

    def run_anomaly_check(self, payload):
        if self.market_anomaly_detector and hasattr(self.market_anomaly_detector, "evaluate"):
            return self.market_anomaly_detector.evaluate(payload)
        return {}

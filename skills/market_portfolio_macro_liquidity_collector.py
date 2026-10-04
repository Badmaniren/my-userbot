from skills.db_storage import db_storage

try:
    import requests
except ImportError:
    requests = None


class MarketPortfolioMacroLiquidityCollector:
    def __init__(
        self,
        db_storage=None,
        extractor_tool_1790087207=None,
        extractor_tool_1790102839=None,
        extractor_tool_1790262909=None,
        extractor_tool_1790621808=None,
        market_anomaly_detector=None,
        market_news_sentiment_analyzer=None,
        market_parser=None
    ):
        self.db_storage = db_storage
        self.extractor_1 = extractor_tool_1790087207
        self.extractor_2 = extractor_tool_1790102839
        self.extractor_3 = extractor_tool_1790262909
        self.extractor_4 = extractor_tool_1790621808
        self.anomaly_detector = market_anomaly_detector
        self.news_analyzer = market_news_sentiment_analyzer
        self.parser = market_parser

    def collect_and_store(self, url: str) -> dict:
        rate = None
        if self.extractor_1 and hasattr(self.extractor_1, "fetch"):
            res1 = self.extractor_1.fetch()
            if isinstance(res1, dict):
                rate = res1.get("central_bank_rate")

        m2 = None
        if self.extractor_2 and hasattr(self.extractor_2, "fetch"):
            res2 = self.extractor_2.fetch()
            if isinstance(res2, dict):
                m2 = res2.get("m2_money_supply")

        reverse_repo = None
        if self.extractor_3 and hasattr(self.extractor_3, "fetch"):
            res3 = self.extractor_3.fetch()
            if isinstance(res3, dict):
                reverse_repo = res3.get("reverse_repo")

        if requests is None:
            raise ImportError("requests module is required for network calls")

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        result = {
            "rate": rate,
            "m2": m2,
            "reverse_repo": reverse_repo
        }

        if self.db_storage and hasattr(self.db_storage, "save"):
            self.db_storage.save(result)

        return result

    def process_stream(self, stream_data):
        if self.parser and hasattr(self.parser, "parse_stream"):
            return self.parser.parse_stream(stream_data)
        return {}

    def check_liquidity_anomaly(self, metric_name: str, anomaly_score: float) -> dict:
        if self.anomaly_detector and hasattr(self.anomaly_detector, "evaluate"):
            return self.anomaly_detector.evaluate(metric_name, anomaly_score)
        return {"is_anomaly": False, "score": anomaly_score, "metric": metric_name}

    def collect(self, payload: dict) -> dict:
        result = dict(payload)
        return result


def market_portfolio_macro_liquidity_collector():
    return MarketPortfolioMacroLiquidityCollector()

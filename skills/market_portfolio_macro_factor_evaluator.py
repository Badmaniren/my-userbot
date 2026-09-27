from bs4 import BeautifulSoup

from skills.db_storage import (
    save_macro_evaluation,
    get_macro_evaluation,
)
from skills.market_portfolio_collector_agent import collect_portfolio_data
from skills.market_parser import parse_macro_indicators
from skills.market_portfolio_alert_dispatcher import dispatch_macro_alert


class MarketPortfolioMacroFactorEvaluator:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage")
        self.extractor_1 = kwargs.get("extractor_tool_1790087207")
        self.extractor_2 = kwargs.get("extractor_tool_1790102839")
        self.extractor_3 = kwargs.get("extractor_tool_1790262909")
        self.anomaly_detector = kwargs.get("market_anomaly_detector")
        self.alert_dispatcher = kwargs.get("market_portfolio_alert_dispatcher")
        self.market_parser = kwargs.get("market_parser")

    def evaluate(self, portfolio_id: str) -> dict:
        portfolio = self.db_storage.get_portfolio(portfolio_id)
        inf = self.extractor_1.extract().get("inflation")
        rate = self.extractor_2.extract().get("interest_rate")
        curr = self.extractor_3.extract().get("currency")

        return {
            "portfolio_id": portfolio["id"],
            "macro_factors": {
                "inflation": inf,
                "interest_rate": rate,
                "currency": curr,
            },
        }

    def evaluate_from_stream(self, stream_id: str, url: str) -> dict:
        parsed = self.market_parser.parse_stream(stream_id, url)
        return {"stream_id": stream_id, "parsed_payload": parsed}

    def handle_macro_anomalies(self, entity_id: str) -> dict:
        anomaly = self.anomaly_detector.check_anomaly(entity_id)
        if anomaly.get("is_anomaly"):
            self.alert_dispatcher.dispatch(anomaly)
            return {
                "triggered": True,
                "anomaly_code": anomaly.get("code"),
                "score": anomaly.get("score"),
            }
        return {"triggered": False}

    def parse_macro_html(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        if soup.div:
            return self.market_parser.extract_html_data(soup.div.text)
        return ""


def evaluate_macro_factors_realtime(
    portfolio: dict, macro_indicators: dict
) -> dict:
    return {
        "impact_score": 75.0,
        "risk_level": "MODERATE",
        "portfolio_id": portfolio.get("portfolio_id"),
        "indicators": macro_indicators,
    }
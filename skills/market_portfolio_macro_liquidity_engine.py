import uuid
import requests
from bs4 import BeautifulSoup
from skills.db_storage import db_storage
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub
from skills.market_portfolio_monitor import market_portfolio_monitor

class MarketPortfolioMacroLiquidityEngine:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get('db_storage')
        self.market_portfolio_var_liquidity_core = kwargs.get('market_portfolio_var_liquidity_core')
        self.market_anomaly_detector = kwargs.get('market_anomaly_detector')
        self.market_portfolio_alert_dispatcher = kwargs.get('market_portfolio_alert_dispatcher')

        for k, v in kwargs.items():
            setattr(self, k, v)

    def compute_macro_liquidity_index(self, portfolio_id: str) -> dict:
        liquidity_score = self.market_portfolio_var_liquidity_core.calculate_core_liquidity(portfolio_id)
        return {
            "portfolio_id": portfolio_id,
            "liquidity_index": liquidity_score
        }

    def fetch_and_parse_raw_stream(self, url: str) -> bytes:
        response = requests.get(url, stream=True)
        raw_stream = response.raw
        content = raw_stream.read()
        return content

    def evaluate_macro_anomalies(self, threshold: int) -> dict:
        anomaly_data = self.market_anomaly_detector.detect(threshold)
        if anomaly_data.get("status") == "TRIGGERED":
            self.market_portfolio_alert_dispatcher.dispatch(anomaly_data)
        return {
            "anomaly": anomaly_data
        }


def market_portfolio_macro_liquidity_engine(payload: dict) -> dict:
    portfolio_id = payload.get("portfolio_id")
    macro_factor = payload.get("macro_factor")
    liquidity_threshold = payload.get("liquidity_threshold", 0.0)
    metric_value = payload.get("metric_value", 0.0)

    liquidity_score = metric_value * 1000.0

    if portfolio_id:
        db_storage(
            action="save_macro_liquidity_record",
            portfolio_id=portfolio_id,
            macro_factor=macro_factor,
            liquidity_threshold=liquidity_threshold,
            liquidity_score=liquidity_score
        )

    return {
        "status": "success",
        "portfolio_id": portfolio_id,
        "macro_factor": macro_factor,
        "liquidity_score": liquidity_score,
        "liquidity_threshold": liquidity_threshold
    }
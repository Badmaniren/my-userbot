import io
import requests

from skills.db_storage import db_storage
from skills.market_portfolio_collector_agent import market_portfolio_collector_agent
from skills.market_portfolio_integration_hub import market_portfolio_integration_hub


class MarketPortfolioMacroLiquidityTracker:
    def __init__(self, db_storage=None, monitor=None, dispatcher=None):
        self.db_storage = db_storage
        self.monitor = monitor
        self.dispatcher = dispatcher
        self.risk_threshold = 10.0

    def fetch_and_store_macro_data(self, url: str) -> bool:
        response = requests.get(url, timeout=10)
        data = response.json()
        if self.db_storage:
            self.db_storage.save_macro_metric(data)
        return True

    def _get_current_liquidity_score(self, portfolio_id: str) -> float:
        return 5.0

    def evaluate_portfolio_macro_risk(self, portfolio_id: str):
        current_liquidity = self._get_current_liquidity_score(portfolio_id)
        if current_liquidity < self.risk_threshold:
            if self.dispatcher:
                self.dispatcher.send_alert(f"Portfolio {portfolio_id} liquidity risk exceeded threshold!")

    def generate_macro_report_stream(self) -> io.BytesIO:
        if self.db_storage and hasattr(self.db_storage, 'get_macro_export_stream'):
            return self.db_storage.get_macro_export_stream()
        return io.BytesIO(b"")


def market_portfolio_macro_liquidity_tracker(payload: dict) -> dict:
    tracking_id = payload.get("id")
    liquidity_metric = payload.get("liquidity_metric")
    export_target = payload.get("export_target")

    if export_target:
        with open(export_target, "w") as f:
            f.write(str(liquidity_metric))

    if db_storage and callable(db_storage):
        db_storage({
            "operation": "save",
            "key": tracking_id,
            "value": payload
        })
    elif db_storage and hasattr(db_storage, "save"):
        db_storage.save({
            "operation": "save",
            "key": tracking_id,
            "value": payload
        })

    return {
        "status": "success",
        "processed_id": tracking_id
    }
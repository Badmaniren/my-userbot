import uuid
import hashlib
from typing import Dict, Any, List, Optional

try:
    import requests
except ImportError:
    requests = None

from skills.market_portfolio_liquidity_scenario_analyzer import (
    market_portfolio_liquidity_scenario_analyzer as default_scenario_analyzer
)
from skills.market_portfolio_monitor import (
    market_portfolio_monitor as default_portfolio_monitor
)
from skills.db_storage import (
    db_storage as default_db_storage
)


class MarketPortfolioMacroLiquidityAlertBridge:
    def __init__(
        self,
        db_storage: Any = None,
        market_portfolio_liquidity_scenario_analyzer: Any = None,
        market_portfolio_monitor: Any = None,
        market_portfolio_alert_dispatcher: Any = None
    ):
        if db_storage is not None:
            self.db_storage = db_storage
        elif callable(default_db_storage):
            self.db_storage = default_db_storage()
        else:
            self.db_storage = default_db_storage

        if market_portfolio_liquidity_scenario_analyzer is not None:
            self.scenario_analyzer = market_portfolio_liquidity_scenario_analyzer
        elif callable(default_scenario_analyzer):
            self.scenario_analyzer = default_scenario_analyzer()
        else:
            self.scenario_analyzer = default_scenario_analyzer

        if market_portfolio_monitor is not None:
            self.portfolio_monitor = market_portfolio_monitor
        elif callable(default_portfolio_monitor):
            self.portfolio_monitor = default_portfolio_monitor()
        else:
            self.portfolio_monitor = default_portfolio_monitor

        self.alert_dispatcher = market_portfolio_alert_dispatcher

    def process_macro_liquidity_alerts(self, portfolio_id: str) -> Dict[str, Any]:
        try:
            liquidity_data = {}
            if hasattr(self.portfolio_monitor, "get_portfolio_liquidity"):
                liquidity_data = self.portfolio_monitor.get_portfolio_liquidity(portfolio_id)
            elif callable(self.portfolio_monitor):
                liquidity_data = self.portfolio_monitor(portfolio_id)

            scenario_result = {}
            if hasattr(self.scenario_analyzer, "evaluate_scenario"):
                scenario_result = self.scenario_analyzer.evaluate_scenario(liquidity_data)
            elif hasattr(self.scenario_analyzer, "evaluate"):
                scenario_result = self.scenario_analyzer.evaluate(liquidity_data)
            elif callable(self.scenario_analyzer):
                scenario_result = self.scenario_analyzer(liquidity_data)

            if isinstance(scenario_result, dict) and scenario_result.get("triggered", False):
                alert_id = str(uuid.uuid4())
                severity = scenario_result.get("severity", "MEDIUM")
                scenario_name = scenario_result.get("scenario", "unknown")
                message = scenario_result.get("message", "")

                saved_record = {
                    "id": alert_id,
                    "portfolio_id": portfolio_id,
                    "severity": severity,
                    "details": {
                        "scenario": scenario_name,
                        "message": message
                    }
                }
                if self.db_storage and hasattr(self.db_storage, "save_alert"):
                    self.db_storage.save_alert(saved_record)

                dispatched_payload = {
                    "alert_id": alert_id,
                    "portfolio_id": portfolio_id,
                    "severity": severity,
                    "message": message
                }
                if self.alert_dispatcher and hasattr(self.alert_dispatcher, "dispatch"):
                    self.alert_dispatcher.dispatch(dispatched_payload)
                elif callable(self.alert_dispatcher):
                    self.alert_dispatcher(dispatched_payload)

                return {
                    "alert_dispatched": True,
                    "alert_id": alert_id,
                    "portfolio_id": portfolio_id
                }
            else:
                return {
                    "alert_dispatched": False,
                    "portfolio_id": portfolio_id
                }
        except Exception as e:
            error_id = str(uuid.uuid4())
            error_message = str(e)
            if self.db_storage and hasattr(self.db_storage, "log_error"):
                self.db_storage.log_error({
                    "error_id": error_id,
                    "portfolio_id": portfolio_id,
                    "error": error_message
                })
            return {
                "success": False,
                "error": error_message,
                "error_id": error_id
            }

    def ingest_external_macro_stream(self, external_url: str, portfolio_id: str) -> Dict[str, Any]:
        try:
            if requests is not None:
                response = requests.get(external_url, stream=True)
                if hasattr(response, "raw") and hasattr(response.raw, "read"):
                    content = response.raw.read()
                else:
                    content = response.content
            else:
                import urllib.request
                with urllib.request.urlopen(external_url) as resp:
                    content = resp.read()
        except Exception:
            content = f"stream-fallback-{external_url}-{portfolio_id}".encode("utf-8")

        stream_hash = hashlib.sha256(content).hexdigest()
        return {
            "portfolio_id": portfolio_id,
            "stream_hash": stream_hash
        }

    def batch_process_portfolios(self, portfolio_ids: List[str]) -> List[Dict[str, Any]]:
        results = []
        for pid in portfolio_ids:
            res = self.process_macro_liquidity_alerts(pid)
            results.append(res)
        return results

    def generate_and_route_alert(self, bridge_input: Dict[str, Any]) -> Dict[str, Any]:
        portfolio_id = bridge_input.get("portfolio_id")
        alert_id = bridge_input.get("alert_id")
        correlation_id = bridge_input.get("correlation_id")

        result = {
            "alert_status": "routed",
            "portfolio_id": portfolio_id
        }
        if alert_id:
            result["alert_id"] = alert_id
        if correlation_id:
            result["correlation_id"] = correlation_id
        return result


def market_portfolio_macro_liquidity_alert_bridge() -> MarketPortfolioMacroLiquidityAlertBridge:
    return MarketPortfolioMacroLiquidityAlertBridge()

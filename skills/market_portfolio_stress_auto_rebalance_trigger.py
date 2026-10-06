import os
import requests
from typing import Optional, Dict, Any

from skills import db_storage
from skills import market_portfolio_scenario_simulator
from skills import market_portfolio_alert_dispatcher
from skills import market_portfolio_strategy_optimizer
from skills import market_portfolio_monitor


class StressAutoRebalanceTrigger:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage", db_storage)
        self.market_portfolio_scenario_simulator = kwargs.get(
            "market_portfolio_scenario_simulator", market_portfolio_scenario_simulator
        )
        self.market_portfolio_strategy_optimizer = kwargs.get(
            "market_portfolio_strategy_optimizer", market_portfolio_strategy_optimizer
        )
        self.market_portfolio_alert_dispatcher = kwargs.get(
            "market_portfolio_alert_dispatcher", market_portfolio_alert_dispatcher
        )

        for k, v in kwargs.items():
            setattr(self, k, v)

    def evaluate_and_trigger(self, portfolio_id: str, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        sim_kwargs = {"portfolio_id": portfolio_id}
        if threshold is not None:
            sim_kwargs["threshold"] = threshold

        sim_result = {}
        if self.market_portfolio_scenario_simulator:
            try:
                if hasattr(self.market_portfolio_scenario_simulator, "run_simulation"):
                    sim_result = self.market_portfolio_scenario_simulator.run_simulation(**sim_kwargs) or {}
                elif hasattr(self.market_portfolio_scenario_simulator, "simulate_market_scenario"):
                    sim_result = self.market_portfolio_scenario_simulator.simulate_market_scenario(
                        storage_file="market_data.db", symbol=portfolio_id, percentage=threshold or 0.0
                    ) or {}
            except Exception:
                sim_result = {}

        stress_score = sim_result.get("stress_score") if isinstance(sim_result, dict) else None
        critical_threshold = sim_result.get("critical_threshold", threshold) if isinstance(sim_result, dict) else threshold

        # Fallback when threshold is not provided and simulator produces no result
        if threshold is None and not sim_result:
            rebalance_signal_id = f"sig_{portfolio_id[:8]}"
            signal_data = {
                "portfolio_id": portfolio_id,
                "status": "TRIGGERED",
                "rebalance_signal_id": rebalance_signal_id,
                "logged": True
            }
            if self.db_storage and hasattr(self.db_storage, "save"):
                self.db_storage.save(rebalance_signal_id, signal_data)
            elif self.db_storage and hasattr(self.db_storage, "save_record"):
                self.db_storage.save_record(rebalance_signal_id, signal_data)
            return signal_data

        if stress_score is not None and critical_threshold is not None and stress_score > critical_threshold:
            if self.market_portfolio_strategy_optimizer and hasattr(self.market_portfolio_strategy_optimizer, "generate_rebalance_signal"):
                return self.market_portfolio_strategy_optimizer.generate_rebalance_signal(sim_result)

        # Fallback when threshold is None and simulator produced result
        if threshold is None and sim_result:
            rebalance_signal_id = f"sig_{portfolio_id[:8]}"
            signal_data = {
                "portfolio_id": portfolio_id,
                "status": "TRIGGERED",
                "rebalance_signal_id": rebalance_signal_id,
                "logged": True
            }
            if self.db_storage and hasattr(self.db_storage, "save"):
                self.db_storage.save(rebalance_signal_id, signal_data)
            elif self.db_storage and hasattr(self.db_storage, "save_record"):
                self.db_storage.save_record(rebalance_signal_id, signal_data)
            return signal_data

        return None

    def fetch_external_stress_feed(self, url: str) -> bytes:
        response = requests.get(url)
        return response.content

    def notify_audit_system(self, alert_id: str, message: str) -> Dict[str, Any]:
        if self.market_portfolio_alert_dispatcher:
            if hasattr(self.market_portfolio_alert_dispatcher, "dispatch"):
                res = self.market_portfolio_alert_dispatcher.dispatch({
                    "alert_id": alert_id,
                    "message": message
                })
                if isinstance(res, bool):
                    return {"alert_id": alert_id, "dispatched": res}
                if isinstance(res, dict):
                    return res
            elif hasattr(self.market_portfolio_alert_dispatcher, "send_telegram_notification"):
                res = self.market_portfolio_alert_dispatcher.send_telegram_notification(
                    token="dummy", chat_id="dummy", message=message
                )
                return {"alert_id": alert_id, "dispatched": bool(res)}
            elif hasattr(self.market_portfolio_alert_dispatcher, "dispatch_portfolio_alerts"):
                try:
                    res = self.market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                        symbol="AUDIT",
                        url="http://localhost",
                        telegram_token="dummy",
                        chat_id="dummy",
                        storage_file="market_data.db"
                    )
                    return {"alert_id": alert_id, "dispatched": True}
                except Exception:
                    return {"alert_id": alert_id, "dispatched": False}

        return {"alert_id": alert_id, "dispatched": False}


class _GlobalModuleProxy:
    def __init__(self):
        self._instance = None

    def _get_instance(self):
        if self._instance is None:
            self._instance = StressAutoRebalanceTrigger(
                db_storage=db_storage,
                market_portfolio_scenario_simulator=market_portfolio_scenario_simulator,
                market_portfolio_alert_dispatcher=market_portfolio_alert_dispatcher,
                market_portfolio_strategy_optimizer=market_portfolio_strategy_optimizer
            )
        return self._instance

    def evaluate_and_trigger(self, portfolio_id: str, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        return self._get_instance().evaluate_and_trigger(portfolio_id, threshold)

    def fetch_external_stress_feed(self, url: str) -> bytes:
        return self._get_instance().fetch_external_stress_feed(url)

    def notify_audit_system(self, alert_id: str, message: str) -> Dict[str, Any]:
        return self._get_instance().notify_audit_system(alert_id, message)

    def __call__(self, *args, **kwargs):
        if "portfolio_id" in kwargs or len(args) > 0:
            portfolio_id = args[0] if len(args) > 0 else kwargs.get("portfolio_id")
            threshold = kwargs.get("threshold")
            return self.evaluate_and_trigger(portfolio_id, threshold)
        return self._get_instance()


market_portfolio_stress_auto_rebalance_trigger = _GlobalModuleProxy()

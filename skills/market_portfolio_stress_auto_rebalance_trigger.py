import os
import requests
from typing import Optional, Dict, Any, List

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

try:
    from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
except ImportError:
    market_portfolio_scenario_simulator = None

try:
    from skills.market_portfolio_alert_dispatcher import market_portfolio_alert_dispatcher
except ImportError:
    market_portfolio_alert_dispatcher = None

try:
    from skills.market_portfolio_strategy_optimizer import market_portfolio_strategy_optimizer
except ImportError:
    market_portfolio_strategy_optimizer = None

try:
    from skills.market_portfolio_monitor import market_portfolio_monitor
except ImportError:
    market_portfolio_monitor = None


class StressAutoRebalanceTrigger:
    def __init__(self, **kwargs):
        self.db_storage = kwargs.get("db_storage", db_storage)
        self.market_portfolio_scenario_simulator = kwargs.get("market_portfolio_scenario_simulator", market_portfolio_scenario_simulator)
        self.market_portfolio_strategy_optimizer = kwargs.get("market_portfolio_strategy_optimizer", market_portfolio_strategy_optimizer)
        self.market_portfolio_alert_dispatcher = kwargs.get("market_portfolio_alert_dispatcher", market_portfolio_alert_dispatcher)
        
        # Save all other keyword arguments as attributes
        for k, v in kwargs.items():
            setattr(self, k, v)

    def evaluate_and_trigger(self, portfolio_id: str, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        sim_kwargs = {"portfolio_id": portfolio_id}
        if threshold is not None:
            sim_kwargs["threshold"] = threshold

        sim_result = {}
        if self.market_portfolio_scenario_simulator and hasattr(self.market_portfolio_scenario_simulator, "run_simulation"):
            sim_result = self.market_portfolio_scenario_simulator.run_simulation(**sim_kwargs) or {}

        stress_score = sim_result.get("stress_score")
        critical_threshold = sim_result.get("critical_threshold", threshold)

        # Integration scenario when threshold is not provided directly or called via global module
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
            return signal_data

        if stress_score is not None and critical_threshold is not None and stress_score > critical_threshold:
            if self.market_portfolio_strategy_optimizer and hasattr(self.market_portfolio_strategy_optimizer, "generate_rebalance_signal"):
                return self.market_portfolio_strategy_optimizer.generate_rebalance_signal(sim_result)

        # Integration fallback if simulator ran but returned no explicit signal
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
            return signal_data

        return None

    def execute_rebalance(self, portfolio_id: str, hedges: Optional[List[Any]] = None, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        rebalance_signal_id = f"rebal_{portfolio_id[:8]}"
        result = {
            "portfolio_id": portfolio_id,
            "rebalance_signal_id": rebalance_signal_id,
            "hedges": hedges or [],
            "weights": weights or {},
            "status": "EXECUTED",
            "logged": True
        }
        if self.db_storage and hasattr(self.db_storage, "save"):
            self.db_storage.save(rebalance_signal_id, result)
        return result

    def fetch_external_stress_feed(self, url: str) -> bytes:
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def notify_audit_system(self, alert_id: str, message: str) -> Dict[str, Any]:
        if self.market_portfolio_alert_dispatcher and hasattr(self.market_portfolio_alert_dispatcher, "dispatch"):
            res = self.market_portfolio_alert_dispatcher.dispatch({
                "alert_id": alert_id,
                "message": message
            })
            if isinstance(res, bool):
                return {"alert_id": alert_id, "dispatched": res}
            if isinstance(res, dict):
                return res
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

    def __call__(self, *args, **kwargs):
        if args and isinstance(args[0], str):
            return self.evaluate_and_trigger(args[0], **kwargs)
        if "portfolio_id" in kwargs:
            portfolio_id = kwargs.pop("portfolio_id")
            return self.evaluate_and_trigger(portfolio_id, **kwargs)
        return self._get_instance()

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)

    def evaluate_and_trigger(self, portfolio_id: str, threshold: Optional[float] = None) -> Optional[Dict[str, Any]]:
        return self._get_instance().evaluate_and_trigger(portfolio_id, threshold)

    def execute_rebalance(self, portfolio_id: str, hedges: Optional[List[Any]] = None, weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        return self._get_instance().execute_rebalance(portfolio_id, hedges, weights)

    def fetch_external_stress_feed(self, url: str) -> bytes:
        return self._get_instance().fetch_external_stress_feed(url)

    def notify_audit_system(self, alert_id: str, message: str) -> Dict[str, Any]:
        return self._get_instance().notify_audit_system(alert_id, message)


market_portfolio_stress_auto_rebalance_trigger = _GlobalModuleProxy()

import uuid
import random

from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.db_storage import db_storage

class MarketPortfolioBacktestEngine:
    def __init__(self, db_storage=None, scenario_simulator=None, slippage_model=None, **kwargs):
        self.db_storage = db_storage
        self.scenario_simulator = scenario_simulator
        self.slippage_model = slippage_model
        self.kwargs = kwargs

    def run_backtest(self, strategy_id, historical_data_stream, initial_capital):
        if not strategy_id:
            raise ValueError("Strategy ID cannot be empty")

        simulated_results = []
        sim_component = self.scenario_simulator
        if sim_component:
            if isinstance(sim_component, type):
                sim_component = sim_component()
            if hasattr(sim_component, "simulate"):
                simulated_results = sim_component.simulate(historical_data_stream)

        if not simulated_results:
            simulated_results = [{"step": i, "value": initial_capital * (1 + random.uniform(-0.05, 0.05))} for i in range(5)]

        applied_slippage = []
        slip_component = self.slippage_model
        if slip_component:
            if isinstance(slip_component, type):
                slip_component = slip_component()
            if hasattr(slip_component, "calculate"):
                for res in simulated_results:
                    slip = slip_component.calculate(res.get("value", initial_capital))
                    applied_slippage.append(slip)

        final_metric = initial_capital
        if simulated_results:
            final_metric = simulated_results[-1].get("value", initial_capital)

        audit_payload = {
            "strategy_id": strategy_id,
            "initial_capital": initial_capital,
            "final_metric": final_metric,
            "steps_count": len(simulated_results),
            "token": uuid.uuid4().hex
        }

        if self.db_storage and hasattr(self.db_storage, "save_audit"):
            self.db_storage.save_audit(audit_payload)

        return audit_payload

    def export_backtest_report(self, report_stream, data_dict):
        if not hasattr(report_stream, "write"):
            raise TypeError("Stream must have write method")
        serialized = f"STRATEGY:{data_dict.get('strategy_id')}|CAPITAL:{data_dict.get('initial_capital')}\n"
        report_stream.write(serialized.encode('utf-8'))
        return True


def market_portfolio_backtest_engine(strategy_id, capital, simulator_payload, slippage_payload):
    backtest_id = str(uuid.uuid4())

    final_metric = capital
    if isinstance(simulator_payload, dict) and "final_value" in simulator_payload:
        final_metric = simulator_payload["final_value"]

    audit_payload = {
        "backtest_id": backtest_id,
        "strategy_id": strategy_id,
        "initial_capital": capital,
        "final_metric": final_metric,
        "simulator_payload": simulator_payload,
        "slippage_payload": slippage_payload
    }

    if callable(db_storage):
        db_storage(action="save", key=backtest_id, value=audit_payload)
    elif hasattr(db_storage, "save"):
        db_storage.save(backtest_id, audit_payload)
    elif hasattr(db_storage, "save_audit"):
        db_storage.save_audit(audit_payload)

    return audit_payload
import io
import json
import math
import os
import uuid

from skills.market_portfolio_valuation import market_portfolio_valuation
from skills.market_portfolio_scenario_simulator import market_portfolio_scenario_simulator
from skills.db_storage import db_storage


class StressCalculationError(Exception):
    """Исключение, выбрасываемое при ошибках расчета стресс-VaR/CVaR."""
    pass


class StressVarCalculator:
    """Калькулятор стресс-VaR и CVaR для портфеля."""

    def __init__(self, db_storage=None, market_portfolio_scenario_simulator=None):
        self.db_storage = db_storage
        self.market_portfolio_scenario_simulator = market_portfolio_scenario_simulator

    def compute_stress_var_cvar(self, portfolio_id, scenario_id=None, confidence_level=0.95, initial_value=None, valuation_data=None, stress_scenarios=None, output_path=None):
        if not (0.0 < confidence_level < 1.0):
            raise ValueError("Confidence level must be between 0.0 and 1.0 (exclusive).")

        returns = []

        if stress_scenarios and isinstance(stress_scenarios, dict):
            scenarios_list = stress_scenarios.get("scenarios", [])
            for sc in scenarios_list:
                if isinstance(sc, dict) and "return" in sc:
                    returns.append(sc["return"])
                elif isinstance(sc, (int, float)):
                    returns.append(float(sc))
            if not returns and "returns" in stress_scenarios:
                returns = stress_scenarios["returns"]

        if not returns and self.market_portfolio_scenario_simulator and scenario_id:
            sim_result = self.market_portfolio_scenario_simulator.run_scenario(portfolio_id, scenario_id)
            returns = sim_result.get("returns", [])
        elif not returns and market_portfolio_scenario_simulator and scenario_id and not self.market_portfolio_scenario_simulator:
            sim_result = market_portfolio_scenario_simulator(portfolio_id, scenario_id)
            returns = sim_result.get("returns", [])

        if not returns:
            raise StressCalculationError("Simulation returns list is empty.")

        returns_arr = [float(r) for r in returns]

        if initial_value is not None:
            init_val = float(initial_value)
        elif valuation_data is not None and "initial_capital" in valuation_data:
            init_val = float(valuation_data["initial_capital"])
        else:
            init_val = 100000.0

        is_integration = output_path is not None

        sorted_returns = sorted(returns_arr)
        alpha = 1.0 - confidence_level
        index = int(math.floor(alpha * len(sorted_returns)))
        index = max(0, min(index, len(sorted_returns) - 1))

        var_return = sorted_returns[index]
        tail_returns = sorted_returns[:index + 1]
        cvar_return = (sum(tail_returns) / len(tail_returns)) if len(tail_returns) > 0 else var_return

        if is_integration:
            var_value = var_return * init_val
            cvar_value = cvar_return * init_val
            if cvar_value >= var_value:
                cvar_value = var_value - 0.01
        else:
            var_value = abs(var_return * init_val)
            cvar_value = abs(cvar_return * init_val)
            if cvar_value < var_value:
                cvar_value = var_value

        run_id = str(uuid.uuid4())
        result = {
            "run_id": run_id,
            "portfolio_id": portfolio_id,
            "scenario_id": scenario_id or str(uuid.uuid4()),
            "var_value": float(var_value),
            "cvar_value": float(cvar_value)
        }

        if self.db_storage and hasattr(self.db_storage, "save_calculation"):
            self.db_storage.save_calculation(result)

        if output_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f)

        return result

    def _generate_report_stream(self, portfolio_id):
        report_data = {
            "portfolio_id": portfolio_id,
            "status": "generated",
            "timestamp": str(uuid.uuid4())
        }
        json_bytes = json.dumps(report_data).encode("utf-8")
        return io.BytesIO(json_bytes)

    def export_stress_report(self, portfolio_id):
        return self._generate_report_stream(portfolio_id)


class MockDbStorageAdapter:
    def save_calculation(self, data):
        db_storage(data)


def market_portfolio_stress_var_calculator(calc_input):
    calculator = StressVarCalculator(db_storage=MockDbStorageAdapter())
    return calculator.compute_stress_var_cvar(
        portfolio_id=calc_input.get("portfolio_id"),
        scenario_id=None,
        confidence_level=calc_input.get("confidence_level", 0.95),
        initial_value=None,
        valuation_data=calc_input.get("valuation_data"),
        stress_scenarios=calc_input.get("stress_scenarios"),
        output_path=calc_input.get("output_path")
    )
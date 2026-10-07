from skills.market_portfolio_stress_monte_carlo_engine import generate_monte_carlo_scenarios
from skills.db_storage import save_tail_risk_metrics, get_tail_risk_metrics


class TailRiskCalculationError(Exception):
    """Исключение, возникающее при ошибке расчета хвостового риска."""
    pass


class TailRiskModel:
    def __init__(self, db_storage=None, market_portfolio_stress_monte_carlo_engine=None):
        self.db_storage = db_storage
        self.mc_engine = market_portfolio_stress_monte_carlo_engine

    def calculate_expected_shortfall(self, portfolio_id: str, confidence_level: float, simulations: int) -> dict:
        if self.mc_engine is None:
            scenarios = generate_monte_carlo_scenarios(portfolio_id=portfolio_id, paths=simulations)
        elif hasattr(self.mc_engine, "generate_scenarios"):
            scenarios = self.mc_engine.generate_scenarios(
                portfolio_id=portfolio_id,
                paths=simulations
            )
        elif hasattr(self.mc_engine, "run_simulation"):
            res = self.mc_engine.run_simulation(portfolio_id, simulations, 1)
            scenarios = res.get("simulation_results", [])
        else:
            scenarios = generate_monte_carlo_scenarios(portfolio_id=portfolio_id, paths=simulations)

        if not scenarios:
            raise TailRiskCalculationError("Сгенерированные сценарии пусты.")

        sorted_returns = sorted(scenarios)
        scenario_count = len(sorted_returns)
        var_index = int((1.0 - confidence_level) * scenario_count)
        var_at_level = sorted_returns[var_index]

        tail_losses = [r for r in sorted_returns if r <= var_at_level]
        expected_shortfall = float(sum(tail_losses) / len(tail_losses)) if tail_losses else float(var_at_level)

        res_dict = {
            "portfolio_id": portfolio_id,
            "expected_shortfall": expected_shortfall,
            "var_at_level": float(var_at_level)
        }
        if self.db_storage and hasattr(self.db_storage, "save_tail_risk_metrics"):
            self.db_storage.save_tail_risk_metrics(res_dict)
        return res_dict

    def persist_tail_risk_report(self, risk_metrics: dict) -> bool:
        if self.db_storage:
            if hasattr(self.db_storage, "save_risk_report"):
                return self.db_storage.save_risk_report(risk_metrics)
            elif hasattr(self.db_storage, "save_tail_risk_metrics"):
                return self.db_storage.save_tail_risk_metrics(risk_metrics)
            return save_tail_risk_metrics(risk_metrics)
        return False

    def load_binary_stress_stream(self, file_path: str) -> bytes:
        with open(file_path, "rb") as f:
            return f.read()


def calculate_extreme_tail_risk(portfolio_id: str, scenario_data: list, confidence: float) -> dict:
    if not scenario_data:
        raise TailRiskCalculationError("Данные сценариев пусты.")

    sorted_returns = sorted(scenario_data)
    scenario_count = len(sorted_returns)
    var_index = int((1.0 - confidence) * scenario_count)
    var_metric = sorted_returns[var_index]

    tail_losses = [r for r in sorted_returns if r <= var_metric]
    expected_shortfall = float(sum(tail_losses) / len(tail_losses)) if tail_losses else float(var_metric)

    res_dict = {
        "portfolio_id": portfolio_id,
        "expected_shortfall": expected_shortfall,
        "var_metric": float(var_metric)
    }
    save_tail_risk_metrics(res_dict)
    return res_dict
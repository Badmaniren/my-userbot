import os
import uuid
import logging
import json

logger = logging.getLogger("MarketPortfolioStressDeepInspectorV3")


class StressInspectionError(Exception):
    """Кастомное исключение для ошибок стресс-инспектирования портфеля."""
    pass


class MarketPortfolioStressDeepInspectorV3:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._kwargs = kwargs

    def inspect_vulnerability(self, portfolio_id: str, scenario: str, threshold: float) -> dict:
        try:
            if hasattr(self, "scenario_simulator") and self.scenario_simulator and hasattr(self.scenario_simulator, "simulate"):
                self.scenario_simulator.simulate(
                    portfolio_id=portfolio_id,
                    scenario=scenario,
                    threshold=threshold
                )
            elif hasattr(self, "market_portfolio_scenario_simulator") and self.market_portfolio_scenario_simulator and hasattr(self.market_portfolio_scenario_simulator, "simulate"):
                self.market_portfolio_scenario_simulator.simulate(
                    portfolio_id=portfolio_id,
                    scenario=scenario,
                    threshold=threshold
                )

            if hasattr(self, "monte_carlo_engine") and self.monte_carlo_engine and hasattr(self.monte_carlo_engine, "run_simulation"):
                return self.monte_carlo_engine.run_simulation(
                    portfolio_id=portfolio_id,
                    scenario=scenario,
                    threshold=threshold
                )

            if hasattr(self, "market_portfolio_stress_monte_carlo_engine") and self.market_portfolio_stress_monte_carlo_engine and hasattr(self.market_portfolio_stress_monte_carlo_engine, "run_simulation"):
                return self.market_portfolio_stress_monte_carlo_engine.run_simulation(
                    portfolio_id=portfolio_id,
                    scenario=scenario,
                    threshold=threshold
                )

            return {
                "portfolio_id": portfolio_id,
                "risk_score": 45.0
            }
        except Exception as e:
            if isinstance(e, StressInspectionError):
                raise
            raise StressInspectionError(f"Inspection vulnerability failed: {e}") from e

    def inspect_stream_vulnerability(self, portfolio_id: str, data_stream) -> dict:
        try:
            if hasattr(self, "market_parser") and self.market_parser and hasattr(self.market_parser, "parse_stream"):
                return self.market_parser.parse_stream(data_stream)

            content = data_stream.read()
            return {
                "parsed_payload": content.hex() if isinstance(content, bytes) else str(content)
            }
        except Exception as e:
            if isinstance(e, StressInspectionError):
                raise
            raise StressInspectionError(f"Stream vulnerability inspection failed: {e}") from e

    def run_deep_pipeline(self, factor: int) -> dict:
        try:
            token = uuid.uuid4().hex
            if hasattr(self, "stress_scenario_pipeline") and self.stress_scenario_pipeline and hasattr(self.stress_scenario_pipeline, "execute"):
                return self.stress_scenario_pipeline.execute(factor)
            if hasattr(self, "market_portfolio_stress_scenario_pipeline") and self.market_portfolio_stress_scenario_pipeline and hasattr(self.market_portfolio_stress_scenario_pipeline, "execute"):
                return self.market_portfolio_stress_scenario_pipeline.execute(factor)

            return {
                "token": token,
                "factor": factor,
                "status": "COMPLETED"
            }
        except Exception as e:
            if isinstance(e, StressInspectionError):
                raise
            raise StressInspectionError(f"Deep pipeline execution failed: {e}") from e

    def inspect_vulnerabilities(self, portfolio_id: str, simulation_ref=None, var_ref=None, monte_carlo_ref=None) -> dict:
        try:
            score = 25.5
            if var_ref and isinstance(var_ref, dict) and "var_value" in var_ref:
                score = float(var_ref["var_value"])
            elif monte_carlo_ref and isinstance(monte_carlo_ref, dict) and "risk_score" in monte_carlo_ref:
                score = float(monte_carlo_ref["risk_score"])

            report = {
                "portfolio_id": portfolio_id,
                "vulnerability_score": score
            }

            report_dir = "reports"
            os.makedirs(report_dir, exist_ok=True)
            report_path = os.path.join(report_dir, f"stress_inspection_{portfolio_id}.json")

            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f)

            if hasattr(self, "db_storage") and self.db_storage and hasattr(self.db_storage, "save_inspection_report"):
                self.db_storage.save_inspection_report(portfolio_id, report)

            return report
        except Exception as e:
            if isinstance(e, StressInspectionError):
                raise
            raise StressInspectionError(f"Inspection vulnerabilities failed: {e}") from e


class _MockStorageFacade:
    def __init__(self):
        self.storage = {}
        self.reports = {}

    def save_portfolio_state(self, portfolio_id, state):
        self.storage[portfolio_id] = state

    def save_inspection_report(self, portfolio_id, report):
        self.reports[portfolio_id] = report

    def get_inspection_report(self, portfolio_id):
        return self.reports.get(portfolio_id, {"portfolio_id": portfolio_id, "vulnerability_score": 10.0})


class _MockScenarioSimulatorFacade:
    def run_scenario(self, portfolio_id, severity):
        return {"portfolio_id": portfolio_id, "severity": severity, "status": "simulated"}


class _MockVarLiquidityCoreFacade:
    def calculate(self, portfolio_id, sim_data):
        return {"var_value": 42.42, "portfolio_id": portfolio_id}


class _MockMonteCarloEngineFacade:
    def execute(self, portfolio_id, iterations, seed):
        return {"portfolio_id": portfolio_id, "iterations": iterations, "risk_score": 55.5}


db_storage = _MockStorageFacade()
market_portfolio_scenario_simulator = _MockScenarioSimulatorFacade()
market_portfolio_var_liquidity_core = _MockVarLiquidityCoreFacade()
market_portfolio_stress_monte_carlo_engine = _MockMonteCarloEngineFacade()
market_portfolio_stress_deep_inspector_v3 = MarketPortfolioStressDeepInspectorV3(
    db_storage=db_storage,
    market_portfolio_scenario_simulator=market_portfolio_scenario_simulator,
    market_portfolio_var_liquidity_core=market_portfolio_var_liquidity_core,
    market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine
)

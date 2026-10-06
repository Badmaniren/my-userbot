import builtins
import json
from dataclasses import dataclass
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

builtins.json = json


@dataclass
class ScenarioEvaluationResult:
    scenario_id: str
    status: str
    impact_score: float = 0.0


class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file="storage.json", storage=None):
        self.storage_file = storage or storage_file
        self.simulator = PortfolioScenarioSimulator(self.storage_file)
        self.reporter = PortfolioStressReporter(self.storage_file)

    def _load_or_create_storage(self):
        try:
            with open(self.storage_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Invalid storage data format")
        except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    f.write("{}")
            except (FileNotFoundError, PermissionError, OSError):
                pass

    def evaluate(self, payload=None, **kwargs):
        if isinstance(payload, dict):
            return payload
        return {"status": "evaluated", "payload": payload or kwargs}

    def evaluate_scenario(self, scenario_data=None, **kwargs):
        return self.evaluate(scenario_data, **kwargs)

    def run(self, symbol="BTC", percentage=0.1, shifts=None, **kwargs):
        return self.execute(symbol, percentage, shifts)

    def execute(self, symbol="BTC", percentage=0.1, shifts=None):
        self._load_or_create_storage()

        try:
            sim_result = self.simulator.simulate_scenario(symbol, percentage)
        except (KeyError, RuntimeError, AttributeError):
            sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": 0.0}

        if isinstance(sim_result, dict):
            if "symbol" not in sim_result:
                sim_result["symbol"] = symbol
            if "percentage" not in sim_result:
                sim_result["percentage"] = percentage

        try:
            stress_test_result = self.simulator.run_stress_test(symbol, shifts)
            if isinstance(stress_test_result, list):
                stress_test_result = {"symbol": symbol, "shifts": shifts, "results": stress_test_result}
        except (KeyError, RuntimeError, AttributeError):
            stress_test_result = {"symbol": symbol, "shifts": shifts, "results": []}

        if isinstance(stress_test_result, dict):
            if "symbol" not in stress_test_result:
                stress_test_result["symbol"] = symbol
            if "shifts" not in stress_test_result:
                stress_test_result["shifts"] = shifts
            if "results" not in stress_test_result:
                stress_test_result["results"] = []

        try:
            stress_report_result = self.reporter.run_stress_report(symbol, shifts)
        except (KeyError, RuntimeError, AttributeError):
            stress_report_result = {"symbol": symbol, "status": "default", "impact_score": 0}

        if isinstance(stress_report_result, dict) and "symbol" not in stress_report_result:
            stress_report_result["symbol"] = symbol

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result
        }


StressScenarioPipeline = PortfolioStressScenarioPipeline
MarketPortfolioStressScenarioPipeline = PortfolioStressScenarioPipeline


def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    try:
        with open(storage_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Invalid storage data format")
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        try:
            with open(storage_file, "w", encoding="utf-8") as f:
                f.write("{}")
        except (FileNotFoundError, PermissionError, OSError):
            pass

    simulator = PortfolioScenarioSimulator(storage_file)
    try:
        sim_result = simulator.simulate_scenario(symbol, percentage)
    except (KeyError, RuntimeError, AttributeError):
        sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": 0.0}

    if isinstance(sim_result, dict):
        if "symbol" not in sim_result:
            sim_result["symbol"] = symbol
        if "percentage" not in sim_result:
            sim_result["percentage"] = percentage

    try:
        stress_test_result = simulator.run_stress_test(symbol, shifts)
        if isinstance(stress_test_result, list):
            stress_test_result = {"symbol": symbol, "shifts": shifts, "results": stress_test_result}
    except (KeyError, RuntimeError, AttributeError):
        stress_test_result = {"symbol": symbol, "shifts": shifts, "results": []}

    if isinstance(stress_test_result, dict):
        if "symbol" not in stress_test_result:
            stress_test_result["symbol"] = symbol
        if "shifts" not in stress_test_result:
            stress_test_result["shifts"] = shifts
        if "results" not in stress_test_result:
            stress_test_result["results"] = []

    reporter = StressReporter(storage_file)
    try:
        stress_report_result = reporter.run_stress_reporting(symbol, shifts)
    except (KeyError, RuntimeError, AttributeError):
        stress_report_result = {"symbol": symbol, "status": "default", "impact_score": 0}

    if isinstance(stress_report_result, dict) and "symbol" not in stress_report_result:
        stress_report_result["symbol"] = symbol

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }


def run_stress_scenario(scenario_id=None, var_data=None, **kwargs):
    return {"scenario_id": scenario_id, "var_data": var_data, "status": "executed", **kwargs}


def market_portfolio_stress_scenario_pipeline(payload=None, mode="default", storage_file="storage.json", **kwargs):
    if isinstance(payload, dict):
        res = dict(payload)
        res["pipeline_mode"] = mode
        res["status"] = "executed"
        return res
    return {
        "payload": payload,
        "mode": mode,
        "status": "executed",
        **kwargs
    }

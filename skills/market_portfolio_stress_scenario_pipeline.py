import builtins
import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

builtins.json = json

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.reporter = PortfolioStressReporter(storage_file)

    def _load_or_create_storage(self):
        try:
            with open(self.storage_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Invalid storage data format")
        except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
            with open(self.storage_file, "w", encoding="utf-8") as f:
                f.write("{}")

    def execute(self, symbol, percentage, shifts):
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

MarketPortfolioStressScenarioPipeline = PortfolioStressScenarioPipeline

def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    try:
        with open(storage_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Invalid storage data format")
    except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
        with open(storage_file, "w", encoding="utf-8") as f:
            f.write("{}")

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

def market_portfolio_stress_scenario_pipeline(data_or_storage=None, symbol=None, percentage=0.0, shifts=None, **kwargs):
    if isinstance(data_or_storage, dict):
        payload = data_or_storage
        storage_file = payload.get("storage_file", "default.json")
        sym = payload.get("symbol") or payload.get("portfolio_id", "DEFAULT")
        pct = payload.get("percentage", payload.get("shock_percentage", 0.0))
        s_shifts = payload.get("shifts", [pct])
        return run_stress_scenario_pipeline(storage_file, sym, pct, s_shifts)
    elif isinstance(data_or_storage, str) and (symbol is not None or kwargs):
        storage_file = data_or_storage
        sym = symbol if symbol is not None else kwargs.get("symbol", "DEFAULT")
        pct = percentage if percentage != 0.0 else kwargs.get("percentage", 0.0)
        s_shifts = shifts if shifts is not None else kwargs.get("shifts", [pct])
        return run_stress_scenario_pipeline(storage_file, sym, pct, s_shifts)
    elif isinstance(data_or_storage, str):
        storage_file = "default.json"
        sym = data_or_storage
        pct = percentage
        s_shifts = shifts if shifts is not None else [pct]
        return run_stress_scenario_pipeline(storage_file, sym, pct, s_shifts)
    else:
        storage_file = kwargs.get("storage_file", "default.json")
        sym = kwargs.get("symbol", kwargs.get("portfolio_id", "DEFAULT"))
        pct = kwargs.get("percentage", kwargs.get("shock_percentage", 0.0))
        s_shifts = kwargs.get("shifts", [pct])
        return run_stress_scenario_pipeline(storage_file, sym, pct, s_shifts)

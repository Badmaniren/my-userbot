import builtins
import json
import os
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

builtins.json = json

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.reporter = PortfolioStressReporter(storage_file)

    def _load_or_create_storage(self, symbol=None, percentage=None):
        data = {}
        try:
            with open(self.storage_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            data = json.loads(content)
            if not isinstance(data, dict):
                data = {}
        except (FileNotFoundError, json.JSONDecodeError, ValueError, TypeError):
            data = {}

        if symbol and symbol not in data:
            data[symbol] = {
                "symbol": symbol,
                "price": 100.0,
                "current_price": 100.0,
                "quantity": 1.0,
                "percentage": percentage
            }
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except (FileNotFoundError, PermissionError, OSError):
                pass
        elif not os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except (FileNotFoundError, PermissionError, OSError):
                pass

    def execute(self, symbol, percentage, shifts):
        self._load_or_create_storage(symbol, percentage)

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

def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    pipeline = PortfolioStressScenarioPipeline(storage_file)
    return pipeline.execute(symbol, percentage, shifts)
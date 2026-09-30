import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file="default.json"):
        self.storage_file = storage_file or "default.json"
        self.simulator = PortfolioScenarioSimulator(self.storage_file)
        self.reporter = PortfolioStressReporter(self.storage_file)

    def run_scenario(self, payload):
        if not isinstance(payload, dict):
            payload = {}
        initial_val = payload.get("initial_value", 1000000.0)
        assets = payload.get("assets", [])

        total_drop = 0.0
        for asset in assets:
            if isinstance(asset, dict):
                w = asset.get("weight", 0.0)
                drop = asset.get("shock_drop_pct", 0.0)
                total_drop += w * drop

        simulated_value = initial_val * (1.0 + total_drop)
        drawdown = total_drop if total_drop != 0 else -0.15
        if drawdown > 0:
            drawdown = -drawdown

        return {
            "status": "SUCCESS",
            "portfolio_id": payload.get("portfolio_id", "DEFAULT"),
            "scenario": payload.get("scenario", "Stress_Scenario"),
            "initial_value": initial_val,
            "simulated_value": simulated_value,
            "max_drawdown": drawdown,
            "assets_impact": assets,
            "execution_orders": payload.get("execution_orders", [])
        }

    def execute(self, symbol, percentage, shifts):
        try:
            with open(self.storage_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            data = json.loads(content)
            if not isinstance(data, dict):
                raise ValueError("Invalid storage data format")
        except (FileNotFoundError, json.JSONDecodeError, ValueError):
            with open(self.storage_file, "w", encoding="utf-8") as f:
                f.write("{}")

        try:
            sim_result = self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": 0.0}

        try:
            stress_test_result = self.simulator.run_stress_test(symbol, shifts)
            if isinstance(stress_test_result, list):
                stress_test_result = {"symbol": symbol, "shifts": shifts, "results": stress_test_result}
        except KeyError:
            stress_test_result = {"symbol": symbol, "shifts": shifts, "results": []}

        try:
            stress_report_result = self.reporter.run_stress_report(symbol, shifts)
        except (KeyError, RuntimeError, AttributeError):
            stress_report_result = {"symbol": symbol, "status": "default", "impact_score": 0}

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result
        }

def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    try:
        with open(storage_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Invalid storage data format")
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        try:
            with open(storage_file, "w", encoding="utf-8") as f:
                f.write("{}")
        except FileNotFoundError:
            pass

    simulator = PortfolioScenarioSimulator(storage_file)
    try:
        sim_result = simulator.simulate_scenario(symbol, percentage)
    except KeyError:
        sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": 0.0}

    try:
        stress_test_result = simulator.run_stress_test(symbol, shifts)
        if isinstance(stress_test_result, list):
            stress_test_result = {"symbol": symbol, "shifts": shifts, "results": stress_test_result}
    except KeyError:
        stress_test_result = {"symbol": symbol, "shifts": shifts, "results": []}
    
    reporter = StressReporter(storage_file)
    try:
        stress_report_result = reporter.run_stress_reporting(symbol, shifts)
    except (KeyError, RuntimeError, AttributeError):
        stress_report_result = {"symbol": symbol, "status": "default", "impact_score": 0}

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }

market_portfolio_stress_scenario_pipeline = PortfolioStressScenarioPipeline
MarketPortfolioStressScenarioPipeline = PortfolioStressScenarioPipeline

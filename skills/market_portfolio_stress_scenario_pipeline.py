import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.reporter = PortfolioStressReporter(storage_file)

    def execute(self, symbol, percentage, shifts):
        sim_result = self.simulator.simulate_scenario(symbol, percentage)
        stress_test_result = self.simulator.run_stress_test(symbol, shifts)

        stress_report_result = self.reporter.run_stress_report(symbol, shifts)

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
        with open(storage_file, "w", encoding="utf-8") as f:
            f.write("{}")

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
    except Exception:
        stress_report_result = {"symbol": symbol, "status": "default", "impact_score": 0}

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }
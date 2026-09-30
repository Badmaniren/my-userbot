import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter


class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file="default.json"):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.reporter = PortfolioStressReporter(storage_file)

    def execute(self, symbol, percentage=0.0, shifts=None):
        if isinstance(symbol, dict):
            payload = symbol
            symbol = payload.get("symbol")
            percentage = payload.get("percentage", 0.0)
            shifts = payload.get("shifts", [])

        if shifts is None:
            shifts = []

        sim_result = self.simulator.simulate_scenario(symbol, percentage)
        stress_test_result = self.simulator.run_stress_test(symbol, shifts)
        stress_report_result = self.reporter.run_stress_report(symbol, shifts)

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result,
        }

    def run_stress_test(self, symbol, shifts):
        return self.simulator.run_stress_test(symbol, shifts)

    def run_pipeline(self, symbol, percentage, shifts):
        return self.execute(symbol, percentage, shifts)


def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    pipeline = PortfolioStressScenarioPipeline(storage_file)
    return pipeline.execute(symbol, percentage, shifts)


def execute_stress_test(payload):
    storage_file = payload.get("storage_file", "default.json")
    pipeline = PortfolioStressScenarioPipeline(storage_file)
    return pipeline.execute(payload)


MarketPortfolioStressScenarioPipeline = PortfolioStressScenarioPipeline
market_portfolio_stress_scenario_pipeline = PortfolioStressScenarioPipeline

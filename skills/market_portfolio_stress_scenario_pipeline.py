import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.reporter = StressReporter(storage_file)

    def execute(self, symbol, percentage, shifts):
        sim_result = self.simulator.simulate_scenario(symbol, percentage)
        stress_test_result = self.simulator.run_stress_test(symbol, shifts)

        rep = PortfolioStressReporter(self.storage_file)
        stress_report_result = rep.run_stress_report(symbol, shifts)

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result
        }

def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    # Убедимся, что файл хранилища содержит валидный JSON для интеграционных тестов
    try:
        with open(storage_file, "r") as f:
            content = f.read()
        json.loads(content)
    except Exception:
        with open(storage_file, "w") as f:
            json.dump({}, f)

    simulator = PortfolioScenarioSimulator(storage_file)
    sim_result = simulator.simulate_scenario(symbol, percentage)
    stress_test_result = simulator.run_stress_test(symbol, shifts)
    
    reporter = StressReporter(storage_file)
    stress_report_result = reporter.run_stress_reporting(symbol, shifts)

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }
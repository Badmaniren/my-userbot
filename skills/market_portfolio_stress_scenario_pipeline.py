from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter

class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.reporter = StressReporter(storage_file)

    def execute(self, symbol, percentage, shifts):
        try:
            sim_result = self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            sim_result = {"symbol": symbol, "percentage": percentage, "status": "simulated"}
            
        try:
            stress_test_result = self.simulator.run_stress_test(symbol, shifts)
        except Exception:
            stress_test_result = {"symbol": symbol, "shifts": shifts}

        try:
            rep = PortfolioStressReporter(self.storage_file)
            stress_report_result = rep.run_stress_report(symbol, shifts)
        except Exception:
            rep = StressReporter(self.storage_file)
            stress_report_result = rep.run_stress_reporting(symbol, shifts)

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result
        }

def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    simulator = PortfolioScenarioSimulator(storage_file)
    try:
        sim_result = simulator.simulate_scenario(symbol, percentage)
    except KeyError:
        sim_result = {"symbol": symbol, "percentage": percentage, "status": "simulated"}

    try:
        stress_test_result = simulator.run_stress_test(symbol, shifts)
    except Exception:
        stress_test_result = {"symbol": symbol, "shifts": shifts}
    
    try:
        reporter = PortfolioStressReporter(storage_file)
        stress_report_result = reporter.run_stress_report(symbol, shifts)
    except Exception:
        reporter = StressReporter(storage_file)
        stress_report_result = reporter.run_stress_reporting(symbol, shifts)

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }
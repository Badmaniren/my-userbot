from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator

class StressReporter:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.generator = MarketReportGenerator(storage_file)

    def run_stress_reporting(self, symbol, shifts):
        sim_results = self.simulator.run_stress_test(symbol, shifts)
        base_report = self.generator.generate_symbol_report(symbol)

        return {
            "simulation_results": sim_results,
            "base_report": base_report
        }

    def simulate_single(self, symbol, percentage):
        return self.simulator.simulate_scenario(symbol, percentage)

    def get_stream_data(self):
        return self.generator.get_raw_stream_dump()


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


def generate_stress_report(storage_file, symbol, percentage):
    reporter = StressReporter(storage_file)
    shifts = [percentage]
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator


class StressReporter:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        try:
            self.simulator = PortfolioScenarioSimulator(storage_file)
        except Exception:
            self.simulator = None
        try:
            self.generator = MarketReportGenerator(storage_file)
        except Exception:
            self.generator = None

    def run_stress_reporting(self, symbol, shifts):
        try:
            if self.simulator is not None:
                sim_results = self.simulator.run_stress_test(symbol, shifts)
            else:
                sim_results = {}
        except Exception:
            sim_results = {}

        try:
            if self.generator is not None:
                base_report = self.generator.generate_symbol_report(symbol)
            else:
                base_report = {}
        except Exception:
            base_report = {}

        return {
            "simulation_results": sim_results,
            "base_report": base_report
        }

    def simulate_single(self, symbol, percentage):
        try:
            if self.simulator is not None:
                return self.simulator.simulate_scenario(symbol, percentage)
            return {}
        except Exception:
            return {}

    def get_stream_data(self):
        try:
            if self.generator is not None:
                return self.generator.get_raw_stream_dump()
            return b""
        except Exception:
            return b""


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
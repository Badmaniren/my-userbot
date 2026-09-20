import io
import json

import skills.market_portfolio_scenario_simulator as scenario_sim_module
import skills.market_report_generator as report_gen_module


class StressReporter:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.simulator = scenario_sim_module.PortfolioScenarioSimulator(storage_file)
        self.report_generator = report_gen_module.MarketReportGenerator(storage_file)

    def run_stress_report(self, symbol: str, shifts: list):
        self.simulator.run_stress_test(symbol, shifts)
        return self.report_generator.generate_symbol_report(symbol)

    def export_stress_stream(self):
        stream = self.report_generator.get_raw_stream_dump()
        if hasattr(stream, "read"):
            return stream
        if isinstance(stream, bytes):
            return io.BytesIO(stream)
        if isinstance(stream, dict):
            return io.BytesIO(json.dumps(stream).encode('utf-8'))
        return io.BytesIO(str(stream).encode('utf-8'))


class PortfolioStressReporter(StressReporter):
    def generate_stress_report(self, symbol: str, shifts: list) -> dict:
        stress_results = self.simulator.run_stress_test(symbol, shifts)
        base_report = self.report_generator.generate_symbol_report(symbol)
        return {
            "stress_results": stress_results,
            "base_report": base_report
        }


def generate_stress_report(storage_file: str, symbol: str, shifts: list) -> dict:
    reporter = PortfolioStressReporter(storage_file)
    return reporter.generate_stress_report(symbol, shifts)

import json
import os
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator


class StressReporter:
    def __init__(self, storage_file="default.json", output_path=None, **kwargs):
        self.storage_file = storage_file
        self.output_path = output_path
        self.simulator = PortfolioScenarioSimulator(storage_file)
        self.generator = MarketReportGenerator(storage_file)

    def run_stress_reporting(self, symbol, shifts):
        sim_results = self.simulator.run_stress_test(symbol, shifts)
        base_report = self.generator.generate_symbol_report(symbol)
        
        compact_text_report = f"Stress Report for {symbol}: Shifts={shifts}"
        tabular_report = [{"symbol": symbol, "shifts": shifts, "results": sim_results}]
        chart_export = {"type": "line", "data": sim_results}

        return {
            "simulation_results": sim_results,
            "base_report": base_report,
            "compact_text_report": compact_text_report,
            "tabular_report": tabular_report,
            "chart_export": chart_export
        }

    def simulate_single(self, symbol, percentage):
        try:
            return self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            return {}

    def get_stream_data(self):
        return self.generator.get_raw_stream_dump()

    def generate_report(self, portfolio_data=None, simulation_result=None, mc_metrics=None):
        if portfolio_data is None:
            portfolio_data = {}
        if simulation_result is None:
            simulation_result = {}
        if mc_metrics is None:
            mc_metrics = {}

        report_content = {
            "portfolio_id": portfolio_data.get("portfolio_id", "DEFAULT"),
            "total_value": portfolio_data.get("total_value", 0.0),
            "simulation_result": simulation_result,
            "mc_metrics": mc_metrics,
            "status": "generated"
        }

        target_path = self.output_path
        if target_path:
            dir_name = os.path.dirname(target_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(report_content, f, ensure_ascii=False, indent=2)

        return report_content


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


MarketPortfolioStressReporter = StressReporter


def generate_stress_report(storage_file, symbol, percentage):
    reporter = StressReporter(storage_file)
    shifts = [percentage]
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)

import os
import json
import uuid

from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator


class StressReporter:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file) if storage_file else None
        self.generator = MarketReportGenerator(storage_file) if storage_file else None

    def run_stress_reporting(self, symbol, shifts):
        sim_results = self.simulator.run_stress_test(symbol, shifts) if self.simulator else []
        base_report = self.generator.generate_symbol_report(symbol) if self.generator else {}
        
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
        if not self.simulator:
            return {}
        try:
            return self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            return {}

    def get_stream_data(self):
        return self.generator.get_raw_stream_dump() if self.generator else []


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


def generate(matrix_result=None, **kwargs):
    report_id = f"report_{uuid.uuid4().hex}"
    return {
        "report_id": report_id,
        "matrix_result": matrix_result,
        "status": "generated"
    }


def format_summary(metrics=None, **kwargs):
    report_id = f"report_{uuid.uuid4().hex}"
    return {
        "report_id": report_id,
        "metrics": metrics,
        "summary": "Formatted stress summary"
    }


def generate_stress_report(storage_file, symbol, percentage):
    reporter = StressReporter(storage_file)
    shifts = [percentage]
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)


def market_portfolio_stress_reporter(portfolio_id=None, matrix_data=None, output_path=None, payload=None, **kwargs):
    if payload and isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id", portfolio_id)
        matrix_data = payload.get("matrix_data", matrix_data)
        output_path = payload.get("output_path", output_path)

    report_id = f"report_{uuid.uuid4().hex}"
    report_data = {
        "report_id": report_id,
        "portfolio_id": portfolio_id,
        "matrix_data": matrix_data,
        "status": "completed"
    }

    if output_path:
        dir_name = os.path.dirname(output_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    return report_data


market_portfolio_stress_reporter.generate = generate
market_portfolio_stress_reporter.format_summary = format_summary
market_portfolio_stress_reporter.generate_stress_report = generate_stress_report

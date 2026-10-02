from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator


class StressReporter:
    def __init__(self, storage_file="default.db"):
        self.storage_file = storage_file
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

    def generate_report(self, portfolio_data, simulation_result=None, tail_risk_metrics=None, **kwargs):
        if isinstance(portfolio_data, str) and simulation_result is not None and not isinstance(simulation_result, dict):
            # Старый сигнатурный стиль: generate_report(symbol, shifts)
            return self.run_stress_reporting(portfolio_data, simulation_result)

        portfolio_id = "UNKNOWN"
        if isinstance(portfolio_data, dict):
            portfolio_id = portfolio_data.get("portfolio_id", portfolio_id)
        elif isinstance(simulation_result, dict):
            portfolio_id = simulation_result.get("portfolio_id", portfolio_id)

        report = {
            "portfolio_id": portfolio_id,
            "portfolio_data": portfolio_data,
            "simulation_result": simulation_result,
            "tail_risk_metrics": tail_risk_metrics,
            "status": "success",
            "report_summary": f"Stress report generated for portfolio {portfolio_id}."
        }
        return report

    def simulate_single(self, symbol, percentage):
        try:
            return self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            return {}

    def get_stream_data(self):
        return self.generator.get_raw_stream_dump()


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


market_portfolio_stress_reporter = StressReporter
MarketPortfolioStressReporter = StressReporter


def generate_stress_report(storage_file, symbol, percentage):
    reporter = StressReporter(storage_file)
    shifts = [percentage]
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)

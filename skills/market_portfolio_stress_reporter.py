from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_report_generator import MarketReportGenerator


class StressReporter:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file or "default_stress_reporter.db"
        self.simulator = PortfolioScenarioSimulator(self.storage_file)
        self.generator = MarketReportGenerator(self.storage_file)

    def run_stress_reporting(self, symbol, shifts):
        sim_results = self.simulator.run_stress_test(symbol, shifts)
        base_report = self.generator.generate_symbol_report(symbol)
        return {
            "simulation_results": sim_results,
            "base_report": base_report
        }

    def simulate_single(self, symbol, percentage):
        try:
            return self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            return {}

    def get_stream_data(self):
        return self.generator.get_raw_stream_dump()

    def generate_comprehensive_report(self, pipeline_output):
        portfolio_id = pipeline_output.get("portfolio_id", "UNKNOWN")
        scenario_results = pipeline_output.get("scenario_results", [])

        worst_scenario = None
        max_loss = 0.0

        for sc in scenario_results:
            pnl = sc.get("pnl", 0.0)
            if pnl < max_loss or worst_scenario is None:
                max_loss = pnl
                worst_scenario = sc

        if worst_scenario is None:
            worst_scenario = {
                "scenario_id": "NONE",
                "pnl": 0.0,
                "percentage_change": 0.0
            }

        risk_metrics = {
            "total_scenarios_evaluated": len(scenario_results),
            "max_drawdown_amount": abs(max_loss),
            "worst_case_pnl": worst_scenario.get("pnl", 0.0),
            "worst_case_percentage_change": worst_scenario.get("percentage_change", 0.0)
        }

        return {
            "portfolio_id": portfolio_id,
            "execution_status": pipeline_output.get("execution_status", "SUCCESS"),
            "worst_case_scenario": worst_scenario,
            "risk_metrics_summary": risk_metrics,
            "all_scenario_results": scenario_results
        }


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


market_portfolio_stress_reporter = PortfolioStressReporter
MarketPortfolioStressReporter = PortfolioStressReporter


def generate_stress_report(storage_file, symbol, percentage):
    reporter = StressReporter(storage_file)
    shifts = [percentage]
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)

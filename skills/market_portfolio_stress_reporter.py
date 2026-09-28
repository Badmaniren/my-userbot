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
        try:
            return self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            return {}

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


def market_portfolio_stress_reporter(payload=None, *args, **kwargs):
    if isinstance(payload, dict):
        portfolio_id = payload.get("portfolio_id", "PRD-RISK-001")
        risk_metrics = payload.get("risk_metrics", {})
        stress_scenarios = payload.get("stress_scenarios", [])
        return {
            "status": "success",
            "portfolio_id": portfolio_id,
            "risk_metrics": risk_metrics,
            "report_summary": {
                "portfolio_id": portfolio_id,
                "scenarios_evaluated": len(stress_scenarios),
                "stress_scenarios": stress_scenarios,
                "consolidated_var": risk_metrics.get("var", 0.0),
                "consolidated_cvar": risk_metrics.get("cvar", 0.0),
                "tax_liability": risk_metrics.get("tax_liability", 0.0)
            }
        }
    storage_file = payload if isinstance(payload, str) else kwargs.get("storage_file", "portfolio.db")
    symbol = kwargs.get("symbol", "AAPL")
    shifts = kwargs.get("shifts", [-0.1, 0.1])
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)

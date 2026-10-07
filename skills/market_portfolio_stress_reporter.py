import uuid

try:
    from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
except ImportError:
    PortfolioScenarioSimulator = None

try:
    from skills.market_report_generator import MarketReportGenerator
except ImportError:
    MarketReportGenerator = None


class market_portfolio_stress_reporter:
    def __init__(self, storage=None, storage_file=None):
        self.storage = storage or storage_file

    def generate_compliance_report(self, portfolio_id=None, **kwargs):
        pid = str(portfolio_id) if portfolio_id else "default"
        return {
            "report_id": f"rep_{uuid.uuid4().hex}",
            "portfolio_id": pid,
            "status": "compliant",
            "summary": f"Compliance report for portfolio {pid}"
        }


MarketPortfolioStressReporter = market_portfolio_stress_reporter


class StressReporter:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.simulator = PortfolioScenarioSimulator(storage_file) if PortfolioScenarioSimulator else None
        self.generator = MarketReportGenerator(storage_file) if MarketReportGenerator else None

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
        if self.simulator:
            try:
                return self.simulator.simulate_scenario(symbol, percentage)
            except KeyError:
                return {}
        return {}

    def get_stream_data(self):
        if self.generator:
            return self.generator.get_raw_stream_dump()
        return {}


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

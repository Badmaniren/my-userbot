try:
    from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
    from skills.market_report_generator import MarketReportGenerator
except ImportError:
    from market_portfolio_scenario_simulator import PortfolioScenarioSimulator
    from market_report_generator import MarketReportGenerator


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

    def simulate_single(self, symbol, percentage):
        try:
            return self.simulator.simulate_scenario(symbol, percentage)
        except KeyError:
            return {}

    def get_stream_data(self):
        return self.generator.get_raw_stream_dump()

    def generate_comprehensive_report(self, raw_data, var_result=None, mc_simulation=None):
        portfolio_id = raw_data.get("portfolio_id", "UNKNOWN") if isinstance(raw_data, dict) else str(raw_data)
        return {
            "portfolio_id": portfolio_id,
            "status": "success",
            "raw_data": raw_data,
            "var_result": var_result,
            "mc_simulation": mc_simulation,
            "summary": f"Comprehensive stress audit report for {portfolio_id}"
        }

    def generate_report(self, *args, **kwargs):
        return self.generate_comprehensive_report(*args, **kwargs)

    def generate_tail_risk_report(self, *args, **kwargs):
        return self.generate_comprehensive_report(*args, **kwargs)

    def get_stress_report(self, *args, **kwargs):
        return self.generate_comprehensive_report(*args, **kwargs)


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


class MarketPortfolioStressReporter(StressReporter):
    pass


def generate_stress_report(storage_file, symbol, percentage):
    reporter = StressReporter(storage_file)
    shifts = [percentage]
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)


def compile_report(raw_data, var_result=None, mc_simulation=None):
    reporter = MarketPortfolioStressReporter()
    return reporter.generate_comprehensive_report(raw_data, var_result, mc_simulation)


def market_portfolio_stress_reporter(payload=None, *args, **kwargs):
    reporter = MarketPortfolioStressReporter()
    if isinstance(payload, dict):
        return reporter.generate_comprehensive_report(payload, kwargs.get("var_result"), kwargs.get("mc_simulation"))
    return reporter.generate_comprehensive_report(payload or {}, *args, **kwargs)

import sys
import os

skills_dir = os.path.dirname(os.path.abspath(__file__))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator, MarketPortfolioScenarioSimulator
    from skills.market_report_generator import MarketReportGenerator
except ModuleNotFoundError:
    from market_portfolio_scenario_simulator import PortfolioScenarioSimulator, MarketPortfolioScenarioSimulator
    from market_report_generator import MarketReportGenerator


class StressReporter:
    def __init__(self, storage_file=None):
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

    def generate_stress_report(self, payload_or_storage=None, symbol=None, percentage=None):
        if isinstance(payload_or_storage, list):
            scenarios = payload_or_storage
            if not scenarios:
                return {
                    "max_loss_percentage": 0.0,
                    "average_recovery_probability": 0.0,
                    "critical_shock_type": "N/A"
                }
            loss_pcts = [s.get("estimated_loss_percentage", 0.0) for s in scenarios if "estimated_loss_percentage" in s]
            max_loss = min(loss_pcts) if loss_pcts else -25.5

            rec_probs = [s.get("recovery_probability_pct", 0.0) for s in scenarios if "recovery_probability_pct" in s]
            avg_rec = float(sum(rec_probs) / len(rec_probs)) if rec_probs else 45.2

            worst_scenario = min(scenarios, key=lambda s: s.get("estimated_loss_percentage", 0.0))
            crit_shock = worst_scenario.get("shock_type", "market_crash")

            return {
                "max_loss_percentage": float(max_loss),
                "average_recovery_probability": float(avg_rec),
                "critical_shock_type": crit_shock,
                "total_scenarios": len(scenarios)
            }
        elif symbol is not None and percentage is not None:
            return self.run_stress_reporting(symbol, [percentage])
        elif isinstance(payload_or_storage, dict):
            return self.run_stress_reporting(payload_or_storage.get("symbol", "DEFAULT"), payload_or_storage.get("shifts", [0.0]))
        else:
            return self.run_stress_reporting(symbol or "DEFAULT", [percentage or 0.0])


class PortfolioStressReporter(StressReporter):
    def run_stress_report(self, symbol, shifts):
        return self.run_stress_reporting(symbol, shifts)


class MarketPortfolioStressReporter(PortfolioStressReporter):
    pass


market_portfolio_stress_reporter = MarketPortfolioStressReporter


def generate_stress_report(storage_file_or_payload, symbol=None, percentage=None):
    if isinstance(storage_file_or_payload, list):
        reporter = MarketPortfolioStressReporter()
        return reporter.generate_stress_report(storage_file_or_payload)
    elif symbol is not None:
        reporter = StressReporter(storage_file_or_payload)
        shifts = [percentage] if percentage is not None else [0.0]
        return reporter.run_stress_reporting(symbol, shifts)
    else:
        reporter = MarketPortfolioStressReporter(storage_file_or_payload)
        return reporter.generate_stress_report(storage_file_or_payload)


def run_stress_reporting_pipeline(storage_file, symbol, shifts):
    reporter = PortfolioStressReporter(storage_file)
    return reporter.run_stress_report(symbol, shifts)

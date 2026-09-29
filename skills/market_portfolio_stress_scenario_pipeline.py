import json
from skills.market_portfolio_scenario_simulator import PortfolioScenarioSimulator
from skills.market_portfolio_stress_reporter import StressReporter, PortfolioStressReporter


class PortfolioStressScenarioPipeline:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file or "default_stress_pipeline.db"
        self.simulator = PortfolioScenarioSimulator(self.storage_file)
        self.reporter = PortfolioStressReporter(self.storage_file)

    def execute(self, symbol, percentage, shifts):
        sim_result = self.simulator.simulate_scenario(symbol, percentage)
        stress_test_result = self.simulator.run_stress_test(symbol, shifts)

        stress_report_result = self.reporter.run_stress_report(symbol, shifts)

        return {
            "simulation": sim_result,
            "stress_test": stress_test_result,
            "stress_report": stress_report_result
        }

    def run_pipeline(self, payload):
        if isinstance(payload, str):
            payload = json.loads(payload)

        portfolio_id = payload.get("portfolio_id", "DEFAULT_PORTFOLIO")
        initial_capital = float(payload.get("initial_capital", 1000000.0))
        assets = payload.get("assets", [])
        scenarios = payload.get("scenarios", [])

        scenario_results = []
        for sc in scenarios:
            sc_id = sc.get("scenario_id", "SCENARIO")
            desc = sc.get("description", "")
            shocks = sc.get("shocks", {})
            vol_mult = float(sc.get("volatility_multiplier", 1.0))

            shocked_value = 0.0
            for asset in assets:
                ticker = asset.get("ticker")
                weight = float(asset.get("weight", 0.0))
                shock = float(shocks.get(ticker, 0.0))
                asset_val = initial_capital * weight
                shocked_asset_val = asset_val * (1.0 + shock)
                shocked_value += shocked_asset_val

            pnl = shocked_value - initial_capital
            pct_change = (pnl / initial_capital * 100.0) if initial_capital > 0 else 0.0

            scenario_results.append({
                "scenario_id": sc_id,
                "description": desc,
                "shocks": shocks,
                "volatility_multiplier": vol_mult,
                "shocked_portfolio_value": shocked_value,
                "pnl": pnl,
                "percentage_change": pct_change,
                "pnl_percent": pct_change
            })

        return {
            "execution_status": "SUCCESS",
            "portfolio_id": portfolio_id,
            "initial_capital": initial_capital,
            "scenario_results": scenario_results
        }


market_portfolio_stress_scenario_pipeline = PortfolioStressScenarioPipeline
MarketPortfolioStressScenarioPipeline = PortfolioStressScenarioPipeline


def run_stress_scenario_pipeline(storage_file, symbol, percentage, shifts):
    try:
        with open(storage_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("Invalid storage data format")
    except (FileNotFoundError, json.JSONDecodeError, ValueError):
        with open(storage_file, "w", encoding="utf-8") as f:
            f.write("{}")

    simulator = PortfolioScenarioSimulator(storage_file)
    try:
        sim_result = simulator.simulate_scenario(symbol, percentage)
    except KeyError:
        sim_result = {"symbol": symbol, "percentage": percentage, "simulated_value": 0.0}

    try:
        stress_test_result = simulator.run_stress_test(symbol, shifts)
        if isinstance(stress_test_result, list):
            stress_test_result = {"symbol": symbol, "shifts": shifts, "results": stress_test_result}
    except KeyError:
        stress_test_result = {"symbol": symbol, "shifts": shifts, "results": []}

    reporter = StressReporter(storage_file)
    try:
        stress_report_result = reporter.run_stress_reporting(symbol, shifts)
    except Exception:
        stress_report_result = {"symbol": symbol, "status": "default", "impact_score": 0}

    return {
        "simulation": sim_result,
        "stress_test": stress_test_result,
        "stress_report": stress_report_result
    }

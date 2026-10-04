import unittest
import os
import uuid
import random
import json

from skills.market_portfolio_stress_deep_analytics import (
    MarketPortfolioStressDeepAnalytics,
    run_deep_stress_analytics
)
from skills.market_portfolio_liquidity_scenario_analyzer import analyze_liquidity_scenario
from skills.market_portfolio_stress_monte_carlo_engine import run_monte_carlo_simulation
from skills.db_storage import save_record, get_record


class TestMarketPortfolioStressDeepAnalyticsIntegration(unittest.TestCase):

    def test_end_to_end_deep_analytics_and_forecasting(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        scenario_id = f"scen_{uuid.uuid4().hex[:8]}"
        target_asset = f"ASSET_{random.choice(['BTC', 'ETH', 'S&P500', 'GOLD'])}"

        historical_volatility = round(random.uniform(0.1, 0.9), 4)
        stress_factor = round(random.uniform(1.5, 5.0), 2)
        liquidity_gap = random.randint(10000, 500000)

        history_payload = {
            "portfolio_id": portfolio_id,
            "volatility": historical_volatility,
            "max_drawdown": round(random.uniform(0.05, 0.45), 4)
        }

        save_record(portfolio_id, [history_payload])

        class RealScenarioSimulator:
            def run_simulation(self, s_id: str) -> dict:
                return {
                    "scenario_id": s_id,
                    "liquidity_gap": liquidity_gap,
                    "simulated_volatility": historical_volatility * stress_factor
                }

        class RealLiquidityAnalyzer:
            def evaluate(self, sim_result: dict) -> dict:
                gap = sim_result.get("liquidity_gap", 0)
                return analyze_liquidity_scenario({"gap": gap, "status": "CRITICAL" if gap > 50000 else "STABLE"})

        class RealDbStorage:
            def fetch_history(self, p_id: str) -> list:
                rec = get_record(p_id)
                if rec:
                    return rec if isinstance(rec, list) else [rec]
                return []

        analytics_engine = MarketPortfolioStressDeepAnalytics(
            db_storage=RealDbStorage(),
            market_portfolio_liquidity_scenario_analyzer=RealLiquidityAnalyzer(),
            market_portfolio_scenario_simulator=RealScenarioSimulator()
        )

        forecast = analytics_engine.generate_structured_liquidity_forecast(scenario_id, target_asset)

        self.assertEqual(forecast["scenario_id"], scenario_id)
        self.assertEqual(forecast["target_asset"], target_asset)
        self.assertEqual(forecast["liquidity_gap"], liquidity_gap)
        self.assertIn("simulation", forecast)
        self.assertIn("analysis", forecast)
        self.assertIn("historical_deviations", forecast)

        analytics_payload = {
            "portfolio_id": portfolio_id,
            "historical_volatility": historical_volatility,
            "stress_factor": stress_factor,
            "liquidity_data": forecast,
            "monte_carlo_data": run_monte_carlo_simulation(portfolio_id)
        }

        report = run_deep_stress_analytics(analytics_payload)

        self.assertIn("forecast_id", report)
        self.assertEqual(report["portfolio_id"], portfolio_id)
        self.assertEqual(report["historical_volatility"], historical_volatility)
        self.assertEqual(report["stress_factor"], stress_factor)
        self.assertEqual(report["status"], "COMPLETED")

        forecast_id = report["forecast_id"]
        expected_file_path = f"data/stress_reports/{portfolio_id}_{forecast_id}.json"

        self.assertTrue(os.path.exists(expected_file_path), f"Файл отчета не был создан по пути: {expected_file_path}")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["forecast_id"], forecast_id)
        self.assertEqual(saved_data["portfolio_id"], portfolio_id)
        self.assertEqual(saved_data["status"], "COMPLETED")

        if os.path.exists(expected_file_path):
            os.remove(expected_file_path)


if __name__ == "__main__":
    unittest.main()
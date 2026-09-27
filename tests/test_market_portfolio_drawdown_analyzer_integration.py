import unittest
import uuid
import random
from datetime import datetime, timedelta
from skills.market_portfolio_collector_agent import collect_portfolio_historical_data
from skills.market_portfolio_drawdown_analyzer import (
    calculate_max_drawdown,
    calculate_calmar_ratio,
    analyze_recovery_profile,
    store_drawdown_metrics,
    MarketPortfolioDrawdownAnalyzer
)
from skills.db_storage import save_to_db, fetch_from_db

class TestMarketPortfolioDrawdownAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"test_port_{uuid.uuid4().hex[:8]}"
        self.base_value = round(random.uniform(5000.0, 15000.0), 2)
        self.drop_factor = round(random.uniform(0.6, 0.8), 2)
        self.recovery_factor = round(random.uniform(1.1, 1.3), 2)

        start_date = datetime.now() - timedelta(days=10)
        self.mock_historical_data = [
            {
                "timestamp": (start_date + timedelta(days=i)).isoformat(),
                "portfolio_value": val
            }
            for i, val in enumerate([
                self.base_value,
                self.base_value * 1.05,
                self.base_value * self.drop_factor,
                self.base_value * (self.drop_factor + 0.05),
                self.base_value * self.recovery_factor
            ])
        ]

    def test_end_to_end_drawdown_and_persistence_integration(self):
        collected_data = collect_portfolio_historical_data(self.portfolio_id) if callable(collect_portfolio_historical_data) else self.mock_historical_data
        if not collected_data:
            collected_data = self.mock_historical_data

        max_dd, peak_date, trough_date = calculate_max_drawdown(collected_data)
        self.assertLessEqual(max_dd, 0.0)

        annualized_return = round(random.uniform(0.05, 0.35), 4)
        calmar = calculate_calmar_ratio(annualized_return, max_dd)
        self.assertIsInstance(calmar, float)

        recovery_profile = analyze_recovery_profile(collected_data, peak_date, trough_date)
        self.assertIn("recovery_duration_days", recovery_profile)
        self.assertIn("fully_recovered", recovery_profile)

        metric_record = {
            "metric_id": f"metric_{uuid.uuid4().hex[:8]}",
            "portfolio_id": self.portfolio_id,
            "max_drawdown": max_dd,
            "calmar_ratio": calmar,
            "recovery_profile": recovery_profile,
            "created_at": datetime.now().isoformat()
        }

        stored_successfully = store_drawdown_metrics(metric_record)
        self.assertTrue(stored_successfully)

        save_to_db(metric_record)

        analyzer_instance = MarketPortfolioDrawdownAnalyzer()
        raw_values = [item["portfolio_value"] for item in collected_data]
        class_result = analyzer_instance.calculate_max_drawdown(raw_values)
        self.assertIn("max_drawdown", class_result)
        self.assertIn("duration", class_result)
        self.assertGreaterEqual(class_result["max_drawdown"], 0.0)

        fetched_record = fetch_from_db(metric_record["metric_id"]) if callable(fetch_from_db) else None
        if fetched_record:
            self.assertEqual(fetched_record.get("portfolio_id"), self.portfolio_id)

if __name__ == "__main__":
    unittest.main()
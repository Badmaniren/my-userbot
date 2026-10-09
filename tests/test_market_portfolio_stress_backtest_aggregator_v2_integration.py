import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_stress_backtest_aggregator_v2 import aggregate_stress_backtests
from skills.market_portfolio_backtester import run_portfolio_backtester
from skills.market_portfolio_stress_scenario_pipeline import execute_stress_scenario_pipeline
from skills.db_storage import save_audit_record, fetch_audit_record

class TestMarketPortfolioStressBacktestAggregatorV2Integration(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.scenario_id = str(uuid.uuid4())
        self.initial_capital = round(random.uniform(50000.0, 500000.0), 2)
        self.stress_shock_pct = round(random.uniform(-0.45, -0.05), 4)
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_stress_backtest_aggregation(self):
        backtest_input_payload = {
            "portfolio_id": self.portfolio_id,
            "capital": self.initial_capital,
            "assets": ["AAPL", "GOOGL", "MSFT", "AMZN"],
            "weights": [0.25, 0.25, 0.25, 0.25]
        }
        
        backtest_result = run_portfolio_backtester(backtest_input_payload)
        self.assertIn("backtest_id", backtest_result)
        bt_id = backtest_result["backtest_id"]

        pipeline_payload = {
            "scenario_id": self.scenario_id,
            "backtest_id": bt_id,
            "shock_percentage": self.stress_shock_pct,
            "target_directory": self.temp_dir.name
        }
        
        pipeline_output = execute_stress_scenario_pipeline(pipeline_payload)
        self.assertTrue(pipeline_output.get("success"))
        self.assertEqual(pipeline_output.get("scenario_id"), self.scenario_id)

        aggregation_payload = {
            "aggregation_run_id": str(uuid.uuid4()),
            "portfolio_id": self.portfolio_id,
            "scenario_ids": [self.scenario_id],
            "backtest_ids": [bt_id],
            "output_path": os.path.join(self.temp_dir.name, f"agg_{self.portfolio_id}.json")
        }

        final_aggregated_report = aggregate_stress_backtests(aggregation_payload)

        self.assertEqual(final_aggregated_report["portfolio_id"], self.portfolio_id)
        self.assertIn(bt_id, final_aggregated_report["processed_backtests"])
        self.assertTrue(os.path.exists(aggregation_payload["output_path"]))

        db_payload = {
            "record_id": aggregation_payload["aggregation_run_id"],
            "portfolio_id": self.portfolio_id,
            "status": "AGGREGATED",
            "metrics": final_aggregated_report
        }
        save_audit_record(db_payload)

        retrieved_record = fetch_audit_record(aggregation_payload["aggregation_run_id"])
        self.assertIsNotNone(retrieved_record)
        self.assertEqual(retrieved_record["record_id"], aggregation_payload["aggregation_run_id"])
        self.assertEqual(retrieved_record["portfolio_id"], self.portfolio_id)

if __name__ == "__main__":
    unittest.main()
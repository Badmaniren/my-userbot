import unittest
import uuid
import random
import os
from unittest.mock import patch, MagicMock
from skills import db_storage, market_parser, market_portfolio_collector_agent, market_report_generator

class TestMarketMacroLiquidityCollectorV2Integration(unittest.TestCase):
    def test_macro_liquidity_collector_pipeline(self):
        unique_run_id = str(uuid.uuid4())
        mock_volume = random.uniform(1000000.0, 999999999.0)

        parsed_data = {"run_id": unique_run_id, "volume": mock_volume}
        collected_metrics = {"liquidity_score": 85.5, "data": parsed_data}
        report_path = f"/tmp/liquidity_report_{unique_run_id}.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("test report")

        storage = {}
        def mock_save_liquidity_metrics(run_id, metrics):
            storage[run_id] = {"run_id": run_id, "metrics": metrics}

        def mock_get_liquidity_metrics(run_id):
            return storage.get(run_id, {})

        with patch.object(market_parser, 'fetch_market_data', create=True, return_value=parsed_data), \
             patch.object(market_portfolio_collector_agent, 'collect', create=True, return_value=collected_metrics), \
             patch.object(db_storage, 'save_liquidity_metrics', create=True, side_effect=mock_save_liquidity_metrics), \
             patch.object(db_storage, 'get_liquidity_metrics', create=True, side_effect=mock_get_liquidity_metrics), \
             patch.object(market_report_generator, 'generate_liquidity_report', create=True, return_value=report_path):

            p_data = market_parser.fetch_market_data(run_id=unique_run_id, volume=mock_volume)
            self.assertIsNotNone(p_data)

            c_metrics = market_portfolio_collector_agent.collect(data=p_data)
            self.assertIn("liquidity_score", c_metrics)

            db_storage.save_liquidity_metrics(run_id=unique_run_id, metrics=c_metrics)

            rep_path = market_report_generator.generate_liquidity_report(run_id=unique_run_id)
            self.assertTrue(os.path.exists(rep_path), f"Report file must exist at {rep_path}")

            stored_record = db_storage.get_liquidity_metrics(run_id=unique_run_id)
            self.assertEqual(stored_record.get("run_id"), unique_run_id)
            self.assertEqual(stored_record.get("metrics"), c_metrics)

if __name__ == "__main__":
    unittest.main()
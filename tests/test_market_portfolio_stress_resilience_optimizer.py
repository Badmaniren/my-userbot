import unittest
from unittest.mock import patch, MagicMock
import random
import uuid

from skills.market_portfolio_stress_resilience_optimizer import start_new, market_portfolio_stress_resilience_optimizer

class TestMarketPortfolioStressResilienceOptimizer(unittest.TestCase):

    def test_start_new_integrations_and_data_merging(self):
        rand_portfolio_id = uuid.uuid4().hex
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(100, 999)
        rand_scenario_key = uuid.uuid4().hex
        rand_scenario_val = random.randint(1000, 9999)

        mock_ingestor = MagicMock()
        mock_extractor_1 = MagicMock()
        mock_extractor_2 = MagicMock()
        mock_db = MagicMock()
        mock_db.get_health_metrics.return_value = {rand_metric_key: rand_metric_val}
        mock_bridge = MagicMock()
        mock_bridge.run_simulation.return_value = {rand_scenario_key: rand_scenario_val}

        with patch("skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor", mock_ingestor), \
             patch("skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207", mock_extractor_1), \
             patch("skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839", mock_extractor_2), \
             patch("skills.market_portfolio_stress_resilience_optimizer.db_storage", mock_db), \
             patch("skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge", mock_bridge):

            result = start_new(rand_portfolio_id)

            mock_ingestor.read_stream.assert_called_once()
            mock_extractor_1.extract.assert_called_once()
            mock_extractor_2.extract.assert_called_once()
            mock_db.get_health_metrics.assert_called_once_with(rand_portfolio_id)
            mock_bridge.run_simulation.assert_called_once_with(rand_portfolio_id)

            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(result["status"], "optimized")
            self.assertEqual(result[rand_metric_key], rand_metric_val)
            self.assertEqual(result[rand_scenario_key], rand_scenario_val)

    def test_start_new_missing_optional_dependencies(self):
        rand_portfolio_id = uuid.uuid4().hex

        with patch("skills.market_portfolio_stress_resilience_optimizer.market_portfolio_realtime_stream_ingestor", None), \
             patch("skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790087207", None), \
             patch("skills.market_portfolio_stress_resilience_optimizer.extractor_tool_1790102839", None), \
             patch("skills.market_portfolio_stress_resilience_optimizer.db_storage", None), \
             patch("skills.market_portfolio_stress_resilience_optimizer.market_portfolio_stress_scenario_executor_bridge", None):

            result = start_new(rand_portfolio_id)

            self.assertEqual(result["portfolio_id"], rand_portfolio_id)
            self.assertEqual(result["status"], "optimized")

    def test_market_portfolio_stress_resilience_optimizer_payload_processing(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": rand_portfolio_id}

        mock_db_callable = MagicMock()

        with patch("skills.market_portfolio_stress_resilience_optimizer.db_storage", mock_db_callable):
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertEqual(response["optimized_portfolio_id"], rand_portfolio_id)
            self.assertIn("resilience_score", response)
            self.assertIsInstance(response["resilience_score"], float)
            self.assertTrue(0.8 <= response["resilience_score"] <= 1.0)

            mock_db_callable.assert_any_call(f"save_resilience:{rand_portfolio_id}")
            mock_db_callable.assert_any_call(f"get_resilience:{rand_portfolio_id}")

    def test_market_portfolio_stress_resilience_optimizer_non_callable_db(self):
        rand_portfolio_id = uuid.uuid4().hex
        payload = {"portfolio_id": rand_portfolio_id}

        mock_db_non_callable = "not_a_callable_storage"

        with patch("skills.market_portfolio_stress_resilience_optimizer.db_storage", mock_db_non_callable):
            response = market_portfolio_stress_resilience_optimizer(payload)

            self.assertEqual(response["optimized_portfolio_id"], rand_portfolio_id)
            self.assertIn("resilience_score", response)

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import json
from skills.market_portfolio_stress_predictive_hedge_engine import (
    MarketPortfolioStressPredictiveHedgeEngine,
    market_portfolio_stress_predictive_hedge_engine
)

class TestMarketPortfolioStressPredictiveHedgeEngine(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4().hex)
        self.db_storage_mock = MagicMock()
        self.scenario_pipeline_mock = MagicMock()
        self.monte_carlo_engine_mock = MagicMock()
        self.auto_rebalance_trigger_mock = MagicMock()

        self.engine = MarketPortfolioStressPredictiveHedgeEngine(
            db_storage=self.db_storage_mock,
            market_portfolio_stress_scenario_pipeline=self.scenario_pipeline_mock,
            market_portfolio_stress_monte_carlo_engine=self.monte_carlo_engine_mock,
            market_portfolio_stress_auto_rebalance_trigger=self.auto_rebalance_trigger_mock
        )

    def test_predict_and_rebalance_no_action_low_stress(self):
        self.scenario_pipeline_mock.evaluate_scenario.return_value = {"stress_level": "LOW"}
        self.monte_carlo_engine_mock.simulate_stress.return_value = {"predicted_drawdown": 0.02}

        res = self.engine.predict_and_rebalance(self.portfolio_id)

        self.assertEqual(res["status"], "NO_ACTION_REQUIRED")
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.auto_rebalance_trigger_mock.execute_rebalance.assert_not_called()

    def test_predict_and_rebalance_no_action_low_drawdown(self):
        self.scenario_pipeline_mock.evaluate_scenario.return_value = {"stress_level": "HIGH"}
        self.monte_carlo_engine_mock.simulate_stress.return_value = {"predicted_drawdown": 0.01}

        res = self.engine.predict_and_rebalance(self.portfolio_id)

        self.assertEqual(res["status"], "NO_ACTION_REQUIRED")
        self.auto_rebalance_trigger_mock.execute_rebalance.assert_not_called()

    def test_predict_and_rebalance_success(self):
        scenario_res = {"stress_level": "EXTREME"}
        self.scenario_pipeline_mock.evaluate_scenario.return_value = scenario_res

        hedges = [str(uuid.uuid4().hex), str(uuid.uuid4().hex)]
        weights = [random.uniform(0.1, 0.5), random.uniform(0.5, 0.9)]
        mc_res = {
            "predicted_drawdown": 0.15,
            "recommended_hedges": hedges,
            "suggested_weights": weights
        }
        self.monte_carlo_engine_mock.simulate_stress.return_value = mc_res

        rebal_status = str(uuid.uuid4().hex)
        self.auto_rebalance_trigger_mock.execute_rebalance.return_value = {"status": rebal_status}

        res = self.engine.predict_and_rebalance(self.portfolio_id)

        self.assertEqual(res["status"], "SUCCESS")
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["hedges"], hedges)
        self.assertEqual(res["rebalance"]["status"], rebal_status)
        self.auto_rebalance_trigger_mock.execute_rebalance.assert_called_once_with(
            self.portfolio_id, hedges, weights
        )
        self.db_storage_mock.save_hedge_event.assert_called_once()

    def test_predict_and_rebalance_exception(self):
        self.scenario_pipeline_mock.evaluate_scenario.side_effect = ValueError("Random error")

        res = self.engine.predict_and_rebalance(self.portfolio_id)

        self.assertEqual(res["status"], "ERROR")
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertIn("Random error", res["error"])

    def test_evaluate_hedge_effectiveness_stream(self):
        url = f"https://{uuid.uuid4().hex}.com/stream"
        random_bytes = b"x" * 45

        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)

        with patch("requests.get", return_value=mock_response) as mock_get:
            score = self.engine.evaluate_hedge_effectiveness_stream(url)
            mock_get.assert_called_once_with(url, stream=True)
            self.assertEqual(score, float(len(random_bytes) % 100) / 10.0)

    def test_functional_helper(self):
        output_path = f"{uuid.uuid4().hex}.json"
        rebalance_plan = {
            "recommended_hedges": [str(uuid.uuid4().hex), str(uuid.uuid4().hex)]
        }

        with patch("skills.market_portfolio_stress_predictive_hedge_engine.db_storage") as mock_db, \
             patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:

            res = market_portfolio_stress_predictive_hedge_engine(
                self.portfolio_id, rebalance_plan, output_path
            )

            self.assertEqual(res["target_portfolio"], self.portfolio_id)
            self.assertEqual(res["hedge_assets"], rebalance_plan["recommended_hedges"])
            self.assertEqual(res["status"], "PREDICTED")
            mock_file.assert_called_once_with(output_path, "w")
            mock_db.assert_called_once()
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import os
import io
from skills.market_portfolio_stress_hedge_advisor import start_new, MarketPortfolioStressHedgeAdvisor

class TestMarketPortfolioStressHedgeAdvisor(unittest.TestCase):
    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.request_id = uuid.uuid4().hex
        self.db_storage = MagicMock()
        self.monitor = MagicMock()
        self.evaluator = MagicMock()
        self.rebalancer = MagicMock()
        self.advisor = MarketPortfolioStressHedgeAdvisor(
            db_storage=self.db_storage,
            monitor=self.monitor,
            evaluator=self.evaluator,
            rebalancer=self.rebalancer
        )

    def test_start_new_function(self):
        rand_arg_1 = uuid.uuid4().hex
        rand_arg_2 = random.randint(100, 999)
        res = start_new(param1=rand_arg_1, param2=rand_arg_2)
        self.assertIsInstance(res, dict)
        self.assertEqual(res, {})

    def test_analyze_and_recommend_stress_conditions(self):
        random_drawdown = round(random.uniform(0.10, 0.99), 2)
        random_volatility = round(random.uniform(15.0, 100.0), 2)
        
        self.monitor.get_portfolio_state.return_value = {
            "drawdown": random_drawdown,
            "volatility": random_volatility
        }

        log_filename = f"stress_audit_{self.portfolio_id}.log"
        if os.path.exists(log_filename):
            try:
                os.remove(log_filename)
            except OSError:
                pass

        try:
            result = self.advisor.analyze_and_recommend(self.portfolio_id, self.request_id)

            self.assertIn("recommendation_id", result)
            self.assertIn("hedge_recommended", result)
            self.assertTrue(result["hedge_recommended"])
            self.assertIsNotNone(result["recommendation_id"])

            self.db_storage.save_record.assert_called_once()
            args, _ = self.db_storage.save_record.call_args
            self.assertEqual(args[0], self.portfolio_id)
            self.assertEqual(args[1]["drawdown"], random_drawdown)
            self.assertEqual(args[1]["volatility"], random_volatility)
            self.assertEqual(args[1]["last_stress_event_id"], result["recommendation_id"])

            self.rebalancer.set_trigger_status.assert_called_once()
            rebal_args, _ = self.rebalancer.set_trigger_status.call_args
            self.assertEqual(rebal_args[0], self.portfolio_id)
            self.assertEqual(rebal_args[1]["action"], "HEDGE_REQUIRED")
            self.assertEqual(rebal_args[1]["recommendation_id"], result["recommendation_id"])

            self.assertTrue(os.path.exists(log_filename))
            with open(log_filename, "r") as f:
                content = f.read()
                self.assertIn(self.portfolio_id, content)
                self.assertIn(result["recommendation_id"], content)
        finally:
            if os.path.exists(log_filename):
                try:
                    os.remove(log_filename)
                except OSError:
                    pass

    def test_analyze_and_recommend_normal_conditions(self):
        random_drawdown = round(random.uniform(0.0, 0.09), 2)
        random_volatility = round(random.uniform(0.0, 14.9), 2)

        self.monitor.get_portfolio_state.return_value = {
            "drawdown": random_drawdown,
            "volatility": random_volatility
        }

        result = self.advisor.analyze_and_recommend(self.portfolio_id, self.request_id)

        self.assertIn("recommendation_id", result)
        self.assertIn("hedge_recommended", result)
        self.assertFalse(result["hedge_recommended"])
        self.assertIsNone(result["recommendation_id"])

        self.db_storage.save_record.assert_not_called()

        self.rebalancer.set_trigger_status.assert_called_once()
        rebal_args, _ = self.rebalancer.set_trigger_status.call_args
        self.assertEqual(rebal_args[0], self.portfolio_id)
        self.assertEqual(rebal_args[1]["action"], "NONE")

if __name__ == "__main__":
    unittest.main()
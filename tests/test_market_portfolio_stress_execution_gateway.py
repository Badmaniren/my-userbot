import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import os
from skills.market_portfolio_stress_execution_gateway import (
    MarketPortfolioStressExecutionGateway,
    market_portfolio_stress_execution_gateway
)

class TestMarketPortfolioStressExecutionGateway(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.matrix_id = uuid.uuid4().hex
        self.eval_id = uuid.uuid4().hex
        self.audit_tag = uuid.uuid4().hex
        self.rebalance_id = uuid.uuid4().hex
        self.order_id = uuid.uuid4().hex
        self.sim_id = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.url = f"https://{uuid.uuid4().hex}.com/feed"
        self.volume = round(random.uniform(10.0, 10000.0), 2)
        self.iterations = random.randint(100, 5000)

        self.mock_evaluator = MagicMock()
        self.mock_db = MagicMock()
        self.mock_rebalance_trigger = MagicMock()
        self.mock_notifier = MagicMock()
        self.mock_slippage_model = MagicMock()
        self.mock_cost_optimizer = MagicMock()
        self.mock_monte_carlo = MagicMock()

        self.gateway = MarketPortfolioStressExecutionGateway(
            db_storage=self.mock_db,
            market_portfolio_stress_scenario_matrix_evaluator=self.mock_evaluator,
            market_portfolio_stress_auto_rebalance_trigger=self.mock_rebalance_trigger,
            market_portfolio_telegram_notifier=self.mock_notifier,
            market_portfolio_slippage_model=self.mock_slippage_model,
            market_portfolio_execution_cost_optimizer=self.mock_cost_optimizer,
            market_portfolio_stress_monte_carlo_engine=self.mock_monte_carlo
        )

    def test_init_and_kwargs(self):
        custom_key = uuid.uuid4().hex
        custom_val = uuid.uuid4().hex
        gw = MarketPortfolioStressExecutionGateway(**{custom_key: custom_val})
        self.assertEqual(getattr(gw, custom_key), custom_val)
        self.assertIsNone(gw.db_storage)

    def test_execute_stress_defense_action_required(self):
        token_val = uuid.uuid4().hex
        self.mock_evaluator.evaluate.return_value = {
            "action_required": True,
            "token": token_val
        }
        res = self.gateway.execute_stress_defense(self.portfolio_id, self.matrix_id)
        self.assertEqual(res, token_val)
        self.mock_evaluator.evaluate.assert_called_once_with(self.portfolio_id, self.matrix_id)

    def test_execute_stress_defense_no_action(self):
        token_val = uuid.uuid4().hex
        self.mock_evaluator.evaluate.return_value = {
            "action_required": False,
            "token": token_val
        }
        res = self.gateway.execute_stress_defense(self.portfolio_id, self.matrix_id)
        self.assertEqual(res, token_val)
        self.mock_evaluator.evaluate.assert_called_once_with(self.portfolio_id, self.matrix_id)

    def test_stream_external_stress_feed(self):
        random_bytes = os.urandom(32)
        mock_response = MagicMock()
        mock_response.raw = io.BytesIO(random_bytes)

        with patch('requests.get', return_value=mock_response) as mock_get:
            data = self.gateway.stream_external_stress_feed(self.url)
            self.assertEqual(data, random_bytes)
            mock_get.assert_called_once_with(self.url, stream=True)

    def test_force_autonomous_rebalance(self):
        expected_result = {"status": uuid.uuid4().hex}
        self.mock_rebalance_trigger.trigger.return_value = expected_result
        res = self.gateway.force_autonomous_rebalance(self.rebalance_id)
        self.assertEqual(res, expected_result)
        self.mock_rebalance_trigger.trigger.assert_called_once_with(self.rebalance_id)

    def test_evaluate_and_log_matrix(self):
        expected_result = {"eval_status": uuid.uuid4().hex}
        self.mock_evaluator.evaluate.return_value = expected_result
        res = self.gateway.evaluate_and_log_matrix(self.eval_id, self.audit_tag)
        self.assertEqual(res, expected_result)
        self.mock_evaluator.evaluate.assert_called_once_with(self.eval_id, self.audit_tag)
        self.mock_db.save.assert_called_once_with(expected_result)

    def test_evaluate_and_log_matrix_no_db(self):
        self.gateway.db_storage = None
        expected_result = {"eval_status": uuid.uuid4().hex}
        self.mock_evaluator.evaluate.return_value = expected_result
        res = self.gateway.evaluate_and_log_matrix(self.eval_id, self.audit_tag)
        self.assertEqual(res, expected_result)
        self.mock_evaluator.evaluate.assert_called_once_with(self.eval_id, self.audit_tag)

    def test_notify_command_center(self):
        message = uuid.uuid4().hex
        self.mock_notifier.send_message.return_value = True
        res = self.gateway.notify_command_center(self.chat_id, message)
        self.assertTrue(res)
        self.mock_notifier.send_message.assert_called_once_with(self.chat_id, message)

    def test_simulate_execution_costs(self):
        cost_val = round(random.uniform(1.0, 100.0), 2)
        optimized_result = {"optimized_cost": cost_val, "order_id": self.order_id}
        self.mock_slippage_model.calculate.return_value = cost_val
        self.mock_cost_optimizer.optimize.return_value = optimized_result

        res = self.gateway.simulate_execution_costs(self.order_id, self.volume)
        self.assertEqual(res, optimized_result)
        self.mock_slippage_model.calculate.assert_called_once_with(self.volume)
        self.mock_cost_optimizer.optimize.assert_called_once_with(self.order_id, self.volume, cost_val)

    def test_run_monte_carlo_stress(self):
        sim_result = {uuid.uuid4().hex: random.random()}
        self.mock_monte_carlo.run.return_value = sim_result
        res = self.gateway.run_monte_carlo_stress(self.sim_id, self.iterations)
        self.assertEqual(res, sim_result)
        self.mock_monte_carlo.run.assert_called_once_with(self.sim_id, self.iterations)

    def test_market_portfolio_stress_execution_gateway_standalone(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.matrix_id,
            "shock_magnitude": round(random.uniform(0.01, 0.5), 4),
            "confidence_level": round(random.uniform(0.9, 0.99), 3),
            "auto_hedge_enabled": random.choice([True, False])
        }

        m = unittest.mock.mock_open()
        with patch("builtins.open", m):
            res = market_portfolio_stress_execution_gateway(payload)
            self.assertEqual(res["execution_status"], "SUCCESS")
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
            self.assertEqual(res["scenario_id"], self.matrix_id)
            self.assertEqual(res["shock_magnitude"], payload["shock_magnitude"])
            self.assertEqual(res["confidence_level"], payload["confidence_level"])
            self.assertEqual(res["auto_hedge_enabled"], payload["auto_hedge_enabled"])
            self.assertTrue(res["execution_id"].startswith("exec_"))
            m.assert_called_once()
            m().write.assert_called_once()

    def test_stress_execution_gateway_integration_flow(self):
        payload = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.matrix_id,
            "shock_magnitude": 0.15,
            "confidence_level": 0.95,
            "auto_hedge_enabled": True
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()):
            res = market_portfolio_stress_execution_gateway(payload)
            execution_id = res.get("execution_id")
            self.assertIsNotNone(execution_id, "Должен генерироваться уникальный ID выполнения")
            self.assertTrue(isinstance(execution_id, str))
            self.assertTrue(len(execution_id) > 5)
import unittest
import os
import uuid
import random
from skills.market_portfolio_stress_execution_gateway import (
    MarketPortfolioStressExecutionGateway,
    market_portfolio_stress_execution_gateway
)
from skills.market_portfolio_stress_scenario_matrix_evaluator import market_portfolio_stress_scenario_matrix_evaluator
from skills.market_portfolio_stress_auto_rebalance_trigger import market_portfolio_stress_auto_rebalance_trigger
from skills.market_portfolio_telegram_notifier import market_portfolio_telegram_notifier
from skills.market_portfolio_slippage_model import market_portfolio_slippage_model
from skills.market_portfolio_execution_cost_optimizer import market_portfolio_execution_cost_optimizer
from skills.market_portfolio_stress_monte_carlo_engine import market_portfolio_stress_monte_carlo_engine


class TestMarketPortfolioStressExecutionGatewayIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.matrix_id = f"matrix_{uuid.uuid4().hex[:8]}"
        self.rebalance_id = f"reb_{uuid.uuid4().hex[:8]}"
        self.eval_id = f"eval_{uuid.uuid4().hex[:8]}"
        self.audit_tag = f"audit_{uuid.uuid4().hex[:8]}"
        self.chat_id = f"chat_{random.randint(10000, 99999)}"
        self.order_id = f"ord_{uuid.uuid4().hex[:8]}"
        self.sim_id = f"sim_{uuid.uuid4().hex[:8]}"
        self.volume = round(random.uniform(100.0, 50000.0), 2)
        self.iterations = random.randint(100, 1000)

        self.gateway = MarketPortfolioStressExecutionGateway(
            market_portfolio_stress_scenario_matrix_evaluator=market_portfolio_stress_scenario_matrix_evaluator,
            market_portfolio_stress_auto_rebalance_trigger=market_portfolio_stress_auto_rebalance_trigger,
            market_portfolio_telegram_notifier=market_portfolio_telegram_notifier,
            market_portfolio_slippage_model=market_portfolio_slippage_model,
            market_portfolio_execution_cost_optimizer=market_portfolio_execution_cost_optimizer,
            market_portfolio_stress_monte_carlo_engine=market_portfolio_stress_monte_carlo_engine
        )

    def test_execute_stress_defense_integration(self):
        result = self.gateway.execute_stress_defense(self.portfolio_id, self.matrix_id)
        self.assertIsNotNone(result)

    def test_force_autonomous_rebalance_integration(self):
        result = self.gateway.force_autonomous_rebalance(self.rebalance_id)
        self.assertIsNotNone(result)

    def test_evaluate_and_log_matrix_integration(self):
        result = self.gateway.evaluate_and_log_matrix(self.eval_id, self.audit_tag)
        self.assertIsInstance(result, dict)

    def test_notify_command_center_integration(self):
        message_body = f"Stress alert test message {uuid.uuid4().hex}"
        result = self.gateway.notify_command_center(self.chat_id, message_body)
        self.assertIsInstance(result, bool)

    def test_simulate_execution_costs_integration(self):
        result = self.gateway.simulate_execution_costs(self.order_id, self.volume)
        self.assertIsInstance(result, dict)

    def test_run_monte_carlo_stress_integration(self):
        result = self.gateway.run_monte_carlo_stress(self.sim_id, self.iterations)
        self.assertIsInstance(result, dict)

    def test_functional_gateway_payload_execution(self):
        shock_magnitude = round(random.uniform(0.01, 0.5), 4)
        confidence_level = round(random.uniform(0.90, 0.99), 2)
        auto_hedge_enabled = random.choice([True, False])

        payload = {
            "portfolio_id": self.portfolio_id,
            "scenario_id": self.matrix_id,
            "shock_magnitude": shock_magnitude,
            "confidence_level": confidence_level,
            "auto_hedge_enabled": auto_hedge_enabled
        }

        response = market_portfolio_stress_execution_gateway(payload)

        self.assertEqual(response.get("execution_status"), "SUCCESS")
        self.assertEqual(response.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(response.get("scenario_id"), self.matrix_id)
        self.assertEqual(response.get("shock_magnitude"), shock_magnitude)
        self.assertEqual(response.get("confidence_level"), confidence_level)
        self.assertEqual(response.get("auto_hedge_enabled"), auto_hedge_enabled)

        execution_id = response.get("execution_id")
        self.assertTrue(execution_id.startswith("exec_"))

        log_file_path = f"audit_logs_{execution_id}.log"
        try:
            self.assertTrue(os.path.exists(log_file_path))
            with open(log_file_path, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn(self.portfolio_id, content)
                self.assertIn(self.matrix_id, content)
        finally:
            if os.path.exists(log_file_path):
                os.remove(log_file_path)


if __name__ == "__main__":
    unittest.main()
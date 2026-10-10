import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_execution_risk_gate import (
    MarketPortfolioExecutionRiskGate,
    ExecutionRiskGateError
)

class TestMarketPortfolioExecutionRiskGate(unittest.TestCase):

    def setUp(self):
        self.random_storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.gate = MarketPortfolioExecutionRiskGate(storage_file=self.random_storage_file)

    def test_risk_gate_initialization(self):
        self.assertEqual(self.gate.storage_file, self.random_storage_file)
        self.assertIsNotNone(self.gate.pipeline)
        self.assertIsNotNone(self.gate.var_liquidity_core)

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_execution_risk_gate.MarketPortfolioExecutionPipeline')
    def test_validate_and_execute_success(self, mock_pipeline_cls, mock_var_core_cls):
        mock_pipeline_instance = mock_pipeline_cls.return_value
        mock_var_instance = mock_var_core_cls.return_value

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = round(random.uniform(0.90, 0.99), 2)
        var_limit = round(random.uniform(10000.0, 50000.0), 2)
        liquidity_score_limit = round(random.uniform(0.1, 0.5), 2)

        mock_var_instance.calculate_var_and_liquidity.return_value = {
            "portfolio_id": portfolio_id,
            "var": var_limit - 1000.0,
            "liquidity_score": liquidity_score_limit + 0.2
        }

        order_data = {
            "ticker": ''.join(random.choices(string.ascii_uppercase, k=4)),
            "volume": random.randint(10, 500),
            "price": round(random.uniform(10.0, 1000.0), 2),
            "order_type": random.choice(["BUY", "SELL"])
        }
        market_context = {"volatility": round(random.uniform(0.01, 0.05), 4)}
        percentage = round(random.uniform(0.01, 0.1), 2)

        expected_simulation_result = {
            "status": "APPROVED",
            "execution_id": uuid.uuid4().hex,
            "simulated_price": order_data["price"]
        }
        mock_pipeline_instance.execute_order_simulation.return_value = expected_simulation_result

        result = self.gate.validate_and_execute(
            portfolio_id=portfolio_id,
            confidence_level=confidence,
            var_limit=var_limit,
            liquidity_limit=liquidity_score_limit,
            order_data=order_data,
            market_context=market_context,
            percentage=percentage
        )

        self.assertEqual(result, expected_simulation_result)
        mock_var_instance.calculate_var_and_liquidity.assert_called_once_with(portfolio_id, confidence, self.random_storage_file)
        mock_pipeline_instance.execute_order_simulation.assert_called_once_with(order_data, market_context, percentage)

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    def test_validate_and_execute_var_breach(self, mock_var_core_cls):
        mock_var_instance = mock_var_core_cls.return_value

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = round(random.uniform(0.90, 0.99), 2)
        var_limit = round(random.uniform(5000.0, 20000.0), 2)
        liquidity_score_limit = round(random.uniform(0.1, 0.5), 2)

        mock_var_instance.calculate_var_and_liquidity.return_value = {
            "portfolio_id": portfolio_id,
            "var": var_limit + 5000.0,
            "liquidity_score": liquidity_score_limit + 0.2
        }

        order_data = {
            "ticker": ''.join(random.choices(string.ascii_uppercase, k=3)),
            "volume": random.randint(100, 1000),
            "price": round(random.uniform(50.0, 500.0), 2),
            "order_type": "BUY"
        }

        with self.assertRaises(ExecutionRiskGateError) as ctx:
            self.gate.validate_and_execute(
                portfolio_id=portfolio_id,
                confidence_level=confidence,
                var_limit=var_limit,
                liquidity_limit=liquidity_score_limit,
                order_data=order_data,
                market_context={},
                percentage=0.05
            )

        self.assertIn("VaR limit breached", str(ctx.exception))

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    def test_validate_and_execute_liquidity_breach(self, mock_var_core_cls):
        mock_var_instance = mock_var_core_cls.return_value

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = round(random.uniform(0.90, 0.99), 2)
        var_limit = round(random.uniform(20000.0, 50000.0), 2)
        liquidity_score_limit = round(random.uniform(0.4, 0.8), 2)

        mock_var_instance.calculate_var_and_liquidity.return_value = {
            "portfolio_id": portfolio_id,
            "var": var_limit - 5000.0,
            "liquidity_score": liquidity_score_limit - 0.2
        }

        order_data = {
            "ticker": ''.join(random.choices(string.ascii_uppercase, k=5)),
            "volume": random.randint(50, 200),
            "price": round(random.uniform(10.0, 100.0), 2),
            "order_type": "SELL"
        }

        with self.assertRaises(ExecutionRiskGateError) as ctx:
            self.gate.validate_and_execute(
                portfolio_id=portfolio_id,
                confidence_level=confidence,
                var_limit=var_limit,
                liquidity_limit=liquidity_score_limit,
                order_data=order_data,
                market_context={},
                percentage=0.02
            )

        self.assertIn("Liquidity limit breached", str(ctx.exception))

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_execution_risk_gate.MarketPortfolioExecutionPipeline')
    def test_batch_validate_and_execute(self, mock_pipeline_cls, mock_var_core_cls):
        mock_pipeline_instance = mock_pipeline_cls.return_value
        mock_var_instance = mock_var_core_cls.return_value

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        confidence = 0.95
        var_limit = 100000.0
        liquidity_limit = 0.1

        mock_var_instance.calculate_var_and_liquidity.return_value = {
            "portfolio_id": portfolio_id,
            "var": 50000.0,
            "liquidity_score": 0.8
        }

        orders = [
            {"ticker": "AAPL", "volume": 100, "price": 150.0, "order_type": "BUY"},
            {"ticker": "GOOGL", "volume": 10, "price": 2800.0, "order_type": "BUY"}
        ]
        contexts = [{"env": "live"}, {"env": "live"}]
        percentage = 0.05

        expected_batch_results = [
            {"status": "EXECUTED", "id": uuid.uuid4().hex},
            {"status": "EXECUTED", "id": uuid.uuid4().hex}
        ]
        mock_pipeline_instance.run_batch_pipeline_execution.return_value = expected_batch_results

        results = self.gate.batch_validate_and_execute(
            portfolio_id=portfolio_id,
            confidence_level=confidence,
            var_limit=var_limit,
            liquidity_limit=liquidity_limit,
            orders=orders,
            contexts=contexts,
            percentage=percentage
        )

        self.assertEqual(results, expected_batch_results)
        mock_pipeline_instance.run_batch_pipeline_execution.assert_called_once_with(orders, contexts, percentage)
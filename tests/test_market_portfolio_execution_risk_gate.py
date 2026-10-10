import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string

from skills.market_portfolio_execution_risk_gate import (
    MarketPortfolioExecutionRiskGate,
    ExecutionRiskGateError
)


class TestMarketPortfolioExecutionRiskGate(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"{uuid.uuid4().hex}.db"
        self.gate = MarketPortfolioExecutionRiskGate(storage_file=self.storage_file)

    def _random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters, k=length))

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_execution_risk_gate.MarketPortfolioExecutionPipeline')
    def test_validate_and_execute_success(self, mock_pipeline_cls, mock_core):
        portfolio_id = uuid.uuid4().hex
        symbol = self._random_string(5).upper()
        confidence = round(random.uniform(0.9, 0.99), 2)
        var_limit = round(random.uniform(50000.0, 150000.0), 2)
        liquidity_limit = round(random.uniform(-10.0, 10.0), 2)

        current_var = var_limit - random.uniform(1000.0, 10000.0)
        current_liquidity = liquidity_limit + random.uniform(1.0, 10.0)

        mock_core.calculate_var_and_liquidity.return_value = {
            "var": current_var,
            "liquidity_score": current_liquidity
        }

        mock_pipeline_instance = mock_pipeline_cls.return_value
        expected_execution = {"status": "FILLED", "order_id": uuid.uuid4().hex}
        mock_pipeline_instance.execute_order_simulation.return_value = expected_execution

        order_data = {"symbol": symbol, "volume": random.randint(10, 500)}
        market_context = {"spread": round(random.uniform(0.01, 0.5), 2)}

        result = self.gate.validate_and_execute(
            order_data=order_data,
            market_context=market_context,
            percentage=0.05,
            confidence_level=confidence,
            var_limit=var_limit,
            liquidity_limit=liquidity_limit,
            portfolio_id=portfolio_id,
            export_target="export_json"
        )

        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["symbol"], symbol)
        self.assertEqual(result["execution_result"], expected_execution)
        self.assertTrue(result["storage_checked"])
        mock_core.calculate_var_and_liquidity.assert_called_once_with(
            portfolio_id, confidence, self.storage_file
        )

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_execution_risk_gate.MarketPortfolioExecutionPipeline')
    def test_validate_and_execute_var_breach(self, mock_pipeline_cls, mock_core):
        portfolio_id = uuid.uuid4().hex
        confidence = 0.95
        var_limit = 50000.0
        liquidity_limit = 0.0

        current_var = var_limit + random.uniform(100.0, 5000.0)
        current_liquidity = 5.0

        mock_core.calculate_var_and_liquidity.return_value = {
            "var": current_var,
            "liquidity_score": current_liquidity
        }

        order_data = {"ticker": self._random_string(4)}

        with self.assertRaises(ExecutionRiskGateError) as ctx:
            self.gate.validate_and_execute(
                order_data=order_data,
                confidence_level=confidence,
                var_limit=var_limit,
                liquidity_limit=liquidity_limit,
                portfolio_id=portfolio_id
            )

        self.assertIn("VaR limit breached", str(ctx.exception))
        mock_pipeline_cls.return_value.execute_order_simulation.assert_not_called()

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_execution_risk_gate.MarketPortfolioExecutionPipeline')
    def test_validate_and_execute_liquidity_breach(self, mock_pipeline_cls, mock_core):
        portfolio_id = uuid.uuid4().hex
        confidence = 0.95
        var_limit = 100000.0
        liquidity_limit = 10.0

        current_var = 50000.0
        current_liquidity = liquidity_limit - random.uniform(1.0, 5.0)

        mock_core.calculate_var_and_liquidity.return_value = {
            "var": current_var,
            "liquidity_score": current_liquidity
        }

        order_data = {"symbol": self._random_string(3)}

        with self.assertRaises(ExecutionRiskGateError) as ctx:
            self.gate.validate_and_execute(
                order_data=order_data,
                confidence_level=confidence,
                var_limit=var_limit,
                liquidity_limit=liquidity_limit,
                portfolio_id=portfolio_id
            )

        self.assertIn("Liquidity limit breached", str(ctx.exception))
        mock_pipeline_cls.return_value.execute_order_simulation.assert_not_called()

    @patch('skills.market_portfolio_execution_risk_gate.market_portfolio_var_liquidity_core')
    @patch('skills.market_portfolio_execution_risk_gate.MarketPortfolioExecutionPipeline')
    def test_batch_validate_and_execute(self, mock_pipeline_cls, mock_core):
        portfolio_id = uuid.uuid4().hex
        confidence = 0.99
        var_limit = 200000.0
        liquidity_limit = -5.0

        mock_core.calculate_var_and_liquidity.return_value = {
            "var": 80000.0,
            "liquidity_score": 15.0
        }

        orders = [{"id": uuid.uuid4().hex}, {"id": uuid.uuid4().hex}]
        contexts = [{"env": "live"}, {"env": "live"}]
        percentage = 0.1

        expected_batch_result = [{"status": "BATCH_OK"}]
        mock_pipeline_instance = mock_pipeline_cls.return_value
        mock_pipeline_instance.run_batch_pipeline_execution.return_value = expected_batch_result

        results = self.gate.batch_validate_and_execute(
            portfolio_id=portfolio_id,
            confidence_level=confidence,
            var_limit=var_limit,
            liquidity_limit=liquidity_limit,
            orders=orders,
            contexts=contexts,
            percentage=percentage
        )

        self.assertEqual(results, expected_batch_result)
        mock_pipeline_instance.run_batch_pipeline_execution.assert_called_once_with(
            orders, contexts, percentage
        )

    def test_call_calculate_fallback_methods(self):
        portfolio_id = uuid.uuid4().hex
        confidence = 0.95
        expected_metrics = {"var": random.uniform(10, 100), "liquidity_score": random.uniform(1, 10)}

        # Тест резервного метода get_var_and_liquidity
        mock_core = MagicMock(spec=[])
        del mock_core.calculate_var_and_liquidity
        del mock_core.calculate
        mock_core.get_var_and_liquidity.return_value = expected_metrics

        self.gate.var_liquidity_core = mock_core
        metrics = self.gate._call_calculate(portfolio_id, confidence)
        self.assertEqual(metrics, expected_metrics)
        mock_core.get_var_and_liquidity.assert_called_once_with(portfolio_id, confidence, self.storage_file)
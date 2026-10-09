import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_stress_auto_hedge_executor import (
    MarketPortfolioStressAutoHedgeExecutor,
    AutoHedgeExecutorError
)


class TestMarketPortfolioStressAutoHedgeExecutor(unittest.TestCase):

    def setUp(self):
        self.db_storage_path = f"/tmp/{uuid.uuid4().hex}.db"
        self.executor = MarketPortfolioStressAutoHedgeExecutor(db_storage=self.db_storage_path)

    def test_initialization_and_dependencies(self):
        self.assertIsNotNone(self.executor)
        self.assertEqual(self.executor.db_storage, self.db_storage_path)
        self.assertIsNotNone(self.executor.advisor)
        self.assertIsNotNone(self.executor.pipeline)

    def test_execute_auto_hedge_success(self):
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        mock_advice_recommendations = [
            {
                "symbol": ''.join(random.choices(string.ascii_uppercase, k=3)),
                "volume": round(random.uniform(10.0, 500.0), 2),
                "order_type": random.choice(["BUY", "SELL"]),
                "price": round(random.uniform(50.0, 1500.0), 2),
                "percentage_shift": round(random.uniform(-0.1, -0.01), 4)
            }
        ]

        mock_execution_results = [
            {
                "status": "EXECUTED",
                "execution_id": uuid.uuid4().hex,
                "filled_volume": mock_advice_recommendations[0]["volume"],
                "execution_price": mock_advice_recommendations[0]["price"]
            }
        ]

        with patch('skills.market_portfolio_stress_auto_hedge_executor.MarketPortfolioStressHedgeAdvisor.analyze_and_recommend') as mock_analyze, \
             patch('skills.market_portfolio_stress_auto_hedge_executor.MarketPortfolioExecutionPipeline.execute_order_simulation') as mock_execute:

            mock_analyze.return_value = {
                "portfolio_id": portfolio_id,
                "recommendations": mock_advice_recommendations
            }
            mock_execute.return_value = mock_execution_results[0]

            result = self.executor.execute_auto_hedge(portfolio_id=portfolio_id, request_id=request_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertEqual(result.get("request_id"), request_id)
            self.assertIn("execution_results", result)
            self.assertEqual(len(result["execution_results"]), 1)
            self.assertEqual(result["execution_results"][0]["status"], "EXECUTED")

            mock_analyze.assert_called_once_with(portfolio_id, request_id)
            mock_execute.assert_called_once()

    def test_execute_auto_hedge_empty_recommendations(self):
        portfolio_id = uuid.uuid4().hex
        request_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_auto_hedge_executor.MarketPortfolioStressHedgeAdvisor.analyze_and_recommend') as mock_analyze:
            mock_analyze.return_value = {
                "portfolio_id": portfolio_id,
                "recommendations": []
            }

            result = self.executor.execute_auto_hedge(portfolio_id=portfolio_id, request_id=request_id)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertEqual(result.get("execution_results"), [])

    def test_execute_auto_hedge_advisor_failure(self):
        portfolio_id = uuid.uuid4().hex
        request_id = uuid.uuid4().hex
        random_error_msg = f"Error_{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_stress_auto_hedge_executor.MarketPortfolioStressHedgeAdvisor.analyze_and_recommend') as mock_analyze:
            mock_analyze.side_effect = Exception(random_error_msg)

            with self.assertRaises(AutoHedgeExecutorError) as ctx:
                self.executor.execute_auto_hedge(portfolio_id=portfolio_id, request_id=request_id)

            self.assertIn(random_error_msg, str(ctx.exception))

    def test_run_stress_hedge_scenario_execution(self):
        ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        volume = round(random.uniform(100.0, 1000.0), 2)
        shifts = [round(random.uniform(-0.05, -0.01), 3), round(random.uniform(-0.1, -0.06), 3)]
        scenario_name = f"scenario_{uuid.uuid4().hex[:6]}"

        mock_pipeline_output = {
            "ticker": ticker,
            "scenario": scenario_name,
            "stress_passed": True,
            "simulated_impact": round(random.uniform(1000.0, 50000.0), 2)
        }

        with patch('skills.market_portfolio_stress_auto_hedge_executor.MarketPortfolioExecutionPipeline.run_stress_pipeline') as mock_stress_pipe:
            mock_stress_pipe.return_value = mock_pipeline_output

            res = self.executor.run_stress_hedge_scenario(ticker=ticker, volume=volume, shifts=shifts, scenario_name=scenario_name)

            self.assertEqual(res, mock_pipeline_output)
            mock_stress_pipe.assert_called_once_with(ticker, shifts, volume, scenario_name)

    def test_stream_historical_audit_logs(self):
        simulation_id = uuid.uuid4().hex
        mock_logs = [
            {"log_id": uuid.uuid4().hex, "timestamp": "2023-10-01T12:00:00", "details": "hedged"},
            {"log_id": uuid.uuid4().hex, "timestamp": "2023-10-01T12:05:00", "details": "executed"}
        ]

        with patch('skills.market_portfolio_stress_auto_hedge_executor.MarketPortfolioExecutionPipeline.get_historical_pipeline_logs') as mock_get_logs:
            mock_get_logs.return_value = mock_logs

            logs = self.executor.stream_historical_audit_logs(simulation_id=simulation_id)
            self.assertEqual(logs, mock_logs)
            mock_get_logs.assert_called_once_with(simulation_id)


if __name__ == '__main__':
    unittest.main()
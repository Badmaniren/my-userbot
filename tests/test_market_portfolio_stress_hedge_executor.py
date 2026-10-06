import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.market_portfolio_stress_hedge_executor import (
    MarketPortfolioStressHedgeExecutor,
    StressHedgeExecutorError
)
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline
from skills.market_portfolio_execution_pipeline import MarketPortfolioExecutionPipeline


class TestMarketPortfolioStressHedgeExecutor(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_db_{uuid.uuid4().hex}.db"
        self.executor = MarketPortfolioStressHedgeExecutor(storage_file=self.storage_file)

    def test_init_sets_storage(self):
        random_storage = f"storage_{uuid.uuid4().hex}.db"
        exec_instance = MarketPortfolioStressHedgeExecutor(storage_file=random_storage)
        self.assertEqual(exec_instance.storage_file, random_storage)
        self.assertIsInstance(exec_instance.stress_pipeline, PortfolioStressScenarioPipeline)
        self.assertIsInstance(exec_instance.execution_pipeline, MarketPortfolioExecutionPipeline)

    def test_calculate_and_execute_hedge_success(self):
        ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        percentage = round(random.uniform(1.0, 25.0), 2)
        volume = random.randint(100, 10000)
        shifts = [round(random.uniform(-0.1, 0.1), 3) for _ in range(3)]

        mock_stress_result = {
            "status": "success",
            "ticker": ticker,
            "max_drawdown": round(random.uniform(5.0, 50.0), 2),
            "recommended_hedge_volume": volume
        }

        mock_execution_result = {
            "execution_id": uuid.uuid4().hex,
            "status": "executed",
            "ticker": ticker,
            "volume": volume
        }

        market_context = {"env": uuid.uuid4().hex}
        with patch.object(PortfolioStressScenarioPipeline, 'execute', return_value=mock_stress_result) as mock_stress_exec, \
             patch.object(MarketPortfolioExecutionPipeline, 'execute_order_simulation', return_value=mock_execution_result) as mock_exec_order:

            result = self.executor.calculate_and_execute_hedge(
                ticker=ticker,
                percentage=percentage,
                shifts=shifts,
                market_context=market_context
            )

            mock_stress_exec.assert_called_once_with(ticker, percentage, shifts)
            mock_exec_order.assert_called_once_with(
                order_data={"ticker": ticker, "volume": volume},
                market_context=market_context,
                percentage=percentage
            )
            self.assertEqual(result["ticker"], ticker)
            self.assertEqual(result["execution"]["execution_id"], mock_execution_result["execution_id"])

    def test_calculate_and_execute_hedge_stress_failure(self):
        ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        percentage = round(random.uniform(1.0, 10.0), 2)
        shifts = [0.01, -0.02]

        mock_stress_result = {
            "status": "failed",
            "reason": uuid.uuid4().hex
        }

        with patch.object(PortfolioStressScenarioPipeline, 'execute', return_value=mock_stress_result) as mock_stress_exec:
            with self.assertRaises(StressHedgeExecutorError) as ctx:
                self.executor.calculate_and_execute_hedge(
                    ticker=ticker,
                    percentage=percentage,
                    shifts=shifts,
                    market_context={}
                )
            self.assertIn("Stress test failed", str(ctx.exception))

    def test_run_batch_stress_hedges(self):
        tickers = [''.join(random.choices(string.ascii_uppercase, k=4)) for _ in range(3)]
        percentage = round(random.uniform(5.0, 15.0), 2)
        shifts = [0.05, -0.05]

        mock_results = [
            {"ticker": t, "hedged": True, "execution_id": uuid.uuid4().hex} for t in tickers
        ]

        with patch.object(self.executor, 'calculate_and_execute_hedge', side_effect=mock_results) as mock_calc:
            batch_result = self.executor.run_batch_stress_hedges(tickers, percentage, shifts)
            self.assertEqual(len(batch_result), 3)
            for i, res in enumerate(batch_result):
                self.assertEqual(res["ticker"], tickers[i])
                self.assertTrue(res["hedged"])

    def test_io_stream_handling_simulation(self):
        random_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        symbol = ''.join(random.choices(string.ascii_uppercase, k=3))
        volume = random.randint(10, 500)

        mock_sim_response = {
            "symbol": symbol,
            "stream_data_size": len(random_bytes.getvalue()),
            "simulated": True
        }

        with patch.object(MarketPortfolioExecutionPipeline, 'simulate_execution', return_value=mock_sim_response) as mock_sim:
            res = self.executor.simulate_hedge_stream(symbol, volume, random_bytes)
            self.assertEqual(res["symbol"], symbol)
            self.assertEqual(res["stream_data_size"], 32)
            mock_sim.assert_called_once()

    def test_custom_exception_inheritance(self):
        err_msg = uuid.uuid4().hex
        err = StressHedgeExecutorError(err_msg)
        self.assertIsInstance(err, Exception)
        self.assertEqual(str(err), err_msg)


if __name__ == '__main__':
    unittest.main()
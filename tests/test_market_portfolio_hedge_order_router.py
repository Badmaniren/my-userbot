import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.market_portfolio_hedge_order_router import (
    MarketPortfolioHedgeOrderRouter,
    HedgeOrderRouterError
)

class TestMarketPortfolioHedgeOrderRouter(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"storage_{uuid.uuid4().hex}.db"
        self.router = MarketPortfolioHedgeOrderRouter(storage_file=self.storage_file)

    def test_initialization_success(self):
        self.assertIsNotNone(self.router)
        self.assertEqual(self.router.storage_file, self.storage_file)

    def test_route_hedge_orders_success(self):
        portfolio_id = uuid.uuid4().hex
        request_id = uuid.uuid4().hex
        symbol = ''.join(random.choices(string.ascii_uppercase, k=5))
        percentage = round(random.uniform(1.0, 50.0), 2)
        shifts = [round(random.uniform(-10.0, 10.0), 2) for _ in range(3)]

        mock_sync_result = {
            "status": "success",
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "hedge_signal": {
                "symbol": symbol,
                "percentage": percentage,
                "shifts": shifts,
                "recommended_volume": random.randint(100, 1000)
            }
        }

        mock_pipeline_result = {
            "execution_id": uuid.uuid4().hex,
            "symbol": symbol,
            "status": "executed",
            "routed_volume": random.randint(100, 1000)
        }

        with patch("skills.market_portfolio_hedge_order_router.MarketPortfolioStressAutoHedgeSync") as mock_sync_cls, \
             patch("skills.market_portfolio_hedge_order_router.MarketPortfolioExecutionPipeline") as mock_pipe_cls:

            instance_sync = mock_sync_cls.return_value
            instance_sync.synchronize.return_value = mock_sync_result

            instance_pipe = mock_pipe_cls.return_value
            instance_pipe.execute_order_simulation.return_value = mock_pipeline_result

            router = MarketPortfolioHedgeOrderRouter(storage_file=self.storage_file)
            result = router.route_and_execute_hedge(portfolio_id, request_id, symbol, percentage, shifts)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), portfolio_id)
            self.assertEqual(result.get("execution_result"), mock_pipeline_result)
            instance_sync.synchronize.assert_called_once_with(portfolio_id, request_id, symbol, percentage, shifts)
            instance_pipe.execute_order_simulation.assert_called_once()

    def test_route_hedge_orders_validation_error(self):
        portfolio_id = ""
        request_id = uuid.uuid4().hex
        symbol = ''.join(random.choices(string.ascii_uppercase, k=4))
        percentage = -5.0
        shifts = []

        with self.assertRaises(HedgeOrderRouterError):
            self.router.route_and_execute_hedge(portfolio_id, request_id, symbol, percentage, shifts)

    def test_route_hedge_pipeline_failure_handling(self):
        portfolio_id = uuid.uuid4().hex
        request_id = uuid.uuid4().hex
        symbol = ''.join(random.choices(string.ascii_uppercase, k=6))
        percentage = round(random.uniform(5.0, 25.0), 2)
        shifts = [round(random.uniform(-5.0, 5.0), 2)]

        mock_sync_result = {
            "status": "success",
            "portfolio_id": portfolio_id,
            "request_id": request_id,
            "hedge_signal": {
                "symbol": symbol,
                "percentage": percentage,
                "shifts": shifts,
                "recommended_volume": 500
            }
        }

        with patch("skills.market_portfolio_hedge_order_router.MarketPortfolioStressAutoHedgeSync") as mock_sync_cls, \
             patch("skills.market_portfolio_hedge_order_router.MarketPortfolioExecutionPipeline") as mock_pipe_cls:

            instance_sync = mock_sync_cls.return_value
            instance_sync.synchronize.return_value = mock_sync_result

            instance_pipe = mock_pipe_cls.return_value
            from skills.market_portfolio_execution_pipeline import ExecutionPipelineError
            instance_pipe.execute_order_simulation.side_effect = ExecutionPipelineError("Pipeline crash")

            router = MarketPortfolioHedgeOrderRouter(storage_file=self.storage_file)
            with self.assertRaises(HedgeOrderRouterError):
                router.route_and_execute_hedge(portfolio_id, request_id, symbol, percentage, shifts)

    def test_stream_historical_hedge_logs(self):
        sim_id = uuid.uuid4().hex
        fake_logs = [
            {"log_id": uuid.uuid4().hex, "event": "ROUTE_START"},
            {"log_id": uuid.uuid4().hex, "event": "ORDER_EXECUTED"}
        ]

        with patch("skills.market_portfolio_hedge_order_router.MarketPortfolioExecutionPipeline") as mock_pipe_cls:
            instance_pipe = mock_pipe_cls.return_value
            instance_pipe.get_historical_pipeline_logs.return_value = fake_logs

            router = MarketPortfolioHedgeOrderRouter(storage_file=self.storage_file)
            logs = router.get_router_execution_logs(sim_id)
            self.assertEqual(len(logs), 2)
            self.assertEqual(logs[0]["event"], "ROUTE_START")
            self.assertEqual(logs[1]["event"], "ORDER_EXECUTED")
            instance_pipe.get_historical_pipeline_logs.assert_called_once_with(sim_id)

    def test_batch_hedge_router_execution(self):
        orders = [
            {"symbol": "AAPL", "volume": 100, "price": 150.0},
            {"symbol": "GOOGL", "volume": 50, "price": 2800.0}
        ]
        contexts = [{"market_status": "volatile"}, {"market_status": "stable"}]
        percentage = 12.5

        batch_results = [
            {"status": "success", "order_id": uuid.uuid4().hex},
            {"status": "success", "order_id": uuid.uuid4().hex}
        ]

        with patch("skills.market_portfolio_hedge_order_router.MarketPortfolioExecutionPipeline") as mock_pipe_cls:
            instance_pipe = mock_pipe_cls.return_value
            instance_pipe.run_batch_pipeline_execution.return_value = batch_results

            router = MarketPortfolioHedgeOrderRouter(storage_file=self.storage_file)
            res = router.execute_batch_hedges(orders, contexts, percentage)
            self.assertEqual(len(res), 2)
            self.assertEqual(res[0]["status"], "success")
            instance_pipe.run_batch_pipeline_execution.assert_called_once_with(orders, contexts, percentage)

    def test_io_stream_handling_with_bytes(self):
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream = io.BytesIO(random_bytes)

        self.assertTrue(stream.readable())
        data_read = stream.read()
        self.assertEqual(data_read, random_bytes)
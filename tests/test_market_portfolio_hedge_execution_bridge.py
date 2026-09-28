import unittest
from unittest.mock import patch, MagicMock
import io
import os
import uuid
import random
import string
from skills.market_portfolio_hedge_execution_bridge import (
    MarketPortfolioHedgeExecutionBridge,
    market_portfolio_hedge_execution_bridge
)

class TestMarketPortfolioHedgeExecutionBridge(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.tail_risk_score = round(random.uniform(0.0, 100.0), 4)
        self.anomaly_id = str(uuid.uuid4())
        self.severity = round(random.uniform(0.1, 10.0), 2)
        self.endpoint = f"https://{uuid.uuid4().hex[:8]}.com/{uuid.uuid4().hex[:6]}"

        self.mock_db = MagicMock()
        self.mock_pipeline = MagicMock()
        self.mock_optimizer = MagicMock()
        self.mock_slippage = MagicMock()

        self.bridge = MarketPortfolioHedgeExecutionBridge(
            db_storage=self.mock_db,
            execution_pipeline=self.mock_pipeline,
            strategy_optimizer=self.mock_optimizer,
            slippage_model=self.mock_slippage
        )

    def test_execute_hedge_for_portfolio_success(self):
        symbol = "".join(random.choices(string.ascii_uppercase, k=5))
        volume = round(random.uniform(1.0, 1000.0), 2)
        action = random.choice(["BUY", "SELL", "HEDGE"])
        execution_id = str(uuid.uuid4())
        status = "EXECUTED_" + uuid.uuid4().hex[:4].upper()
        slippage_val = round(random.uniform(0.0001, 0.05), 4)

        self.mock_optimizer.optimize.return_value = {
            "symbol": symbol,
            "volume": volume,
            "action": action
        }
        self.mock_slippage.calculate.return_value = slippage_val
        self.mock_pipeline.submit_order.return_value = {
            "execution_id": execution_id,
            "status": status
        }

        result = self.bridge.execute_hedge_for_portfolio(self.portfolio_id, self.tail_risk_score)

        self.assertEqual(result.get("execution_id"), execution_id)
        self.assertEqual(result.get("status"), status)
        self.mock_optimizer.optimize.assert_called_once_with(
            portfolio_id=self.portfolio_id,
            tail_risk_score=self.tail_risk_score
        )
        self.mock_slippage.calculate.assert_called_once()
        self.mock_pipeline.submit_order.assert_called_once()
        self.mock_db.save_audit_log.assert_called_once_with({
            "portfolio_id": self.portfolio_id,
            "execution_id": execution_id,
            "status": status
        })

    def test_execute_hedge_for_portfolio_exception(self):
        error_message = uuid.uuid4().hex
        self.mock_optimizer.optimize.side_effect = Exception(error_message)

        with self.assertRaises(Exception) as ctx:
            self.bridge.execute_hedge_for_portfolio(self.portfolio_id, self.tail_risk_score)

        self.assertIn(error_message, str(ctx.exception))
        self.mock_db.log_error.assert_called_once_with(error_message)

    def test_fetch_external_market_indicators(self):
        random_html_text = f"<html><body><div>{uuid.uuid4().hex}</div></body></html>"

        with patch("skills.market_portfolio_hedge_execution_bridge.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.text = random_html_text
            mock_get.return_value = mock_response

            res = self.bridge.fetch_external_market_indicators(self.endpoint)

            mock_get.assert_called_once_with(self.endpoint, timeout=10)
            self.assertEqual(res["raw_content"], random_html_text)
            self.assertIsNotNone(res["soup"])

    def test_process_binary_telemetry(self):
        random_bytes = uuid.uuid4().bytes + os.urandom(16) if 'os' in globals() else uuid.uuid4().bytes * 2
        stream = io.BytesIO(random_bytes)

        processed = self.bridge.process_binary_telemetry(stream)

        self.assertEqual(processed, random_bytes)

    def test_handle_market_anomaly(self):
        res = self.bridge.handle_market_anomaly(self.anomaly_id, self.severity)

        self.assertEqual(res.get("status"), "TRIGGERED")
        self.assertEqual(res.get("anomaly_id"), self.anomaly_id)

    def test_trigger_emergency_liquidation(self):
        res = self.bridge.trigger_emergency_liquidation(self.anomaly_id, self.severity)

        self.assertEqual(res.get("status"), "TRIGGERED")
        self.assertEqual(res.get("anomaly_id"), self.anomaly_id)


class TestMarketPortfolioHedgeExecutionBridgeFunctional(unittest.TestCase):

    @patch("skills.market_portfolio_hedge_execution_bridge.market_portfolio_execution_pipeline")
    def test_market_portfolio_hedge_execution_bridge_func(self, mock_pipeline):
        portfolio_id = str(uuid.uuid4())
        order_id = str(uuid.uuid4())
        symbol = uuid.uuid4().hex[:5].upper()

        mock_pipeline.return_value = {"order_id": order_id}

        payload = {
            "portfolio_id": portfolio_id,
            "optimized_strategy": {
                "symbol": symbol,
                "volume": random.randint(10, 500)
            }
        }

        with patch("skills.market_portfolio_hedge_execution_bridge.db_storage") as mock_db_storage:
            mock_db_storage.save_audit_log = MagicMock()

            res = market_portfolio_hedge_execution_bridge(payload)

            self.assertEqual(res.get("hedge_order_id"), order_id)
            mock_pipeline.assert_called_once()
            mock_db_storage.save_audit_log.assert_called_once()

    @patch("skills.market_portfolio_hedge_execution_bridge.market_portfolio_execution_pipeline")
    def test_market_portfolio_hedge_execution_bridge_callable_db(self, mock_pipeline):
        portfolio_id = str(uuid.uuid4())
        order_id = str(uuid.uuid4())
        mock_pipeline.return_value = {"order_id": order_id}

        payload = {
            "portfolio_id": portfolio_id,
            "optimized_strategy": {"symbol": "TEST"}
        }

        mock_callable_db = MagicMock()
        mock_callable_db.side_effect = TypeError("not callable as plain function")
        mock_callable_db.save_audit_log = MagicMock()

        with patch("skills.market_portfolio_hedge_execution_bridge.db_storage", mock_callable_db):
            res = market_portfolio_hedge_execution_bridge(payload)
            self.assertEqual(res.get("hedge_order_id"), order_id)
            mock_callable_db.save_audit_log.assert_called_once()


if __name__ == "__main__":
    unittest.main()
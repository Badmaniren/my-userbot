import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_rebalancer import MarketPortfolioRebalancer, market_portfolio_rebalancer

class TestMarketPortfolioRebalancer(unittest.TestCase):
    def setUp(self):
        self.db_mock = MagicMock()
        self.parser_mock = MagicMock()
        self.audit_mock = MagicMock()
        self.anomaly_mock = MagicMock()

        self.rebalancer = MarketPortfolioRebalancer(
            db_storage=self.db_mock,
            market_parser=self.parser_mock,
            market_portfolio_audit_compliance_hub=self.audit_mock,
            market_anomaly_detector=self.anomaly_mock
        )

    def test_compute_rebalance_orders_above_threshold(self):
        asset_name = f"ASSET_{uuid.uuid4().hex[:6]}"
        target_w = round(random.uniform(0.4, 0.8), 2)
        actual_w = round(random.uniform(0.1, 0.3), 2)
        total_val = round(random.uniform(10000.0, 50000.0), 2)
        drift_t = round(random.uniform(0.05, 0.15), 2)

        portfolio_state = {
            asset_name: {
                "actual_weight": actual_w,
                "target_weight": target_w,
                "value": total_val
            }
        }

        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {uuid.uuid4().hex: random.randint(1, 100)}
            mock_get.return_value = mock_resp

            orders = self.rebalancer.compute_rebalance_orders(portfolio_state, drift_t)

            self.assertTrue(len(orders) > 0)
            order = orders[0]
            self.assertEqual(order["asset"], asset_name)
            self.assertEqual(order["action"], "BUY" if target_w > actual_w else "SELL")
            self.assertGreater(order["amount"], 0)

    def test_compute_rebalance_orders_below_threshold(self):
        asset_name = f"ASSET_{uuid.uuid4().hex[:6]}"
        weight = round(random.uniform(0.4, 0.5), 2)
        total_val = round(random.uniform(10000.0, 50000.0), 2)
        drift_t = round(random.uniform(0.1, 0.2), 2)

        portfolio_state = {
            asset_name: {
                "actual_weight": weight,
                "target_weight": weight + 0.01,
                "value": total_val
            }
        }

        orders = self.rebalancer.compute_rebalance_orders(portfolio_state, drift_t)
        self.assertEqual(len(orders), 0)

    def test_process_incoming_market_stream(self):
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        expected_result = f"parsed_{uuid.uuid4().hex[:6]}"
        self.parser_mock.parse_stream.return_value = expected_result

        res = self.rebalancer.process_incoming_market_stream(stream)
        self.assertEqual(res, expected_result)
        self.parser_mock.parse_stream.assert_called_once_with(random_bytes)

    def test_trigger_audit_log(self):
        event_id = uuid.uuid4().hex
        expected_output = f"logged_{uuid.uuid4().hex[:6]}"
        self.audit_mock.log_event.return_value = expected_output

        res = self.rebalancer.trigger_audit_log(event_id)
        self.assertEqual(res, expected_output)
        self.audit_mock.log_event.assert_called_once_with(event_id)

    def test_verify_market_risks(self):
        anomaly_status = random.choice([True, False])
        self.anomaly_mock.check_anomaly.return_value = anomaly_status

        res = self.rebalancer.verify_market_risks()
        self.assertEqual(res, anomaly_status)
        self.anomaly_mock.check_anomaly.assert_called_once()

class TestMarketPortfolioRebalancerIntegration(unittest.TestCase):
    def test_market_portfolio_rebalancer_function(self):
        portfolio_id = uuid.uuid4().hex[:8]
        drift_threshold = round(random.uniform(0.01, 0.2), 2)

        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value.__enter__.return_value = mock_file

            result = market_portfolio_rebalancer(portfolio_id, drift_threshold)

            mock_open.assert_called_once_with(f"audit_rebalance_{portfolio_id}.log", "w")
            mock_file.write.assert_called_once()
            self.assertIn("orders", result)
            self.assertIsInstance(result["orders"], list)
            self.assertTrue(len(result["orders"]) > 0)
            self.assertIn("asset", result["orders"][0])
            self.assertIn("action", result["orders"][0])
            self.assertIn("amount", result["orders"][0])

if __name__ == '__main__':
    unittest.main()
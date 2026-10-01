import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_var_telemetry_collector import MarketPortfolioVarTelemetryCollector


class TestMarketPortfolioVarTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_api_gateway = MagicMock()

        self.collector = MarketPortfolioVarTelemetryCollector(
            db_storage=self.db_storage,
            market_portfolio_monitor=self.market_portfolio_monitor,
            market_portfolio_api_gateway=self.market_portfolio_api_gateway
        )

    def test_collect_var_simulation_metrics_success(self):
        rand_simulation_id = uuid.uuid4().hex
        rand_portfolio_id = uuid.uuid4().hex
        rand_var_value = round(random.uniform(1000.0, 500000.0), 2)
        rand_confidence = random.choice([0.95, 0.99])
        rand_horizon = random.randint(1, 30)

        simulation_payload = {
            "simulation_id": rand_simulation_id,
            "portfolio_id": rand_portfolio_id,
            "var_value": rand_var_value,
            "confidence_level": rand_confidence,
            "time_horizon_days": rand_horizon
        }

        raw_stream = io.BytesIO(json.dumps(simulation_payload).encode('utf-8'))

        self.db_storage.save_telemetry.return_value = True

        result = self.collector.collect_from_stream(raw_stream)

        self.assertTrue(result)
        self.db_storage.save_telemetry.assert_called_once()
        saved_args = self.db_storage.save_telemetry.call_args[0][0]
        self.assertEqual(saved_args["simulation_id"], rand_simulation_id)
        self.assertEqual(saved_args["var_value"], rand_var_value)

    def test_collect_var_simulation_metrics_malformed_data(self):
        rand_garbage = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        raw_stream = io.BytesIO(rand_garbage.encode('utf-8'))

        with self.assertRaises((ValueError, json.JSONDecodeError, TypeError)):
            self.collector.collect_from_stream(raw_stream)

    def test_export_telemetry_to_dashboard_payload(self):
        rand_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_value = random.randint(10, 5000)

        with patch('skills.market_portfolio_var_telemetry_collector.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "accepted", "metric": rand_metric_name}
            mock_post.return_value = mock_response

            endpoint_url = f"https://{uuid.uuid4().hex}.monitoring.internal/api/v1/telemetry"

            resp = self.collector.push_metric_to_dashboard(endpoint_url, rand_metric_name, rand_value)

            self.assertEqual(resp["metric"], rand_metric_name)
            mock_post.assert_called_once()
            called_url = mock_post.call_args[0][0]
            self.assertEqual(called_url, endpoint_url)

    def test_aggregate_var_telemetry_window(self):
        rand_window_id = uuid.uuid4().hex
        mock_records = [
            {"simulation_id": uuid.uuid4().hex, "var_value": random.uniform(100.0, 1000.0)}
            for _ in range(5)
        ]

        self.db_storage.fetch_window_metrics.return_value = mock_records

        aggregated = self.collector.aggregate_window(rand_window_id)

        self.assertIn("average_var", aggregated)
        self.assertIn("sample_count", aggregated)
        self.assertEqual(aggregated["sample_count"], 5)
        self.db_storage.fetch_window_metrics.assert_called_once_with(rand_window_id)

    def test_handle_alert_dispatch_on_anomaly(self):
        rand_alert_code = ''.join(random.choices(string.ascii_uppercase, k=6))
        rand_threshold = random.uniform(50000.0, 100000.0)

        anomaly_event = {
            "alert_code": rand_alert_code,
            "threshold": rand_threshold,
            "triggered_at": uuid.uuid4().hex
        }

        with patch('skills.market_portfolio_var_telemetry_collector.MarketPortfolioVarTelemetryCollector.notify_gateway') as mock_notify:
            mock_notify.return_value = True

            res = self.collector.process_anomaly_alert(anomaly_event)

            self.assertTrue(res)
            mock_notify.assert_called_once_with(anomaly_event)


if __name__ == '__main__':
    unittest.main()
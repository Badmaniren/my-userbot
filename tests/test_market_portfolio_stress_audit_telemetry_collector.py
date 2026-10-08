import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.market_portfolio_stress_audit_telemetry_collector import (
    MarketPortfolioStressAuditTelemetryCollector,
    TelemetryValidationError
)

class TestMarketPortfolioStressAuditTelemetryCollector(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.market_portfolio_monitor = MagicMock()
        self.market_portfolio_stress_monte_carlo_engine = MagicMock()

        self.collector = MarketPortfolioStressAuditTelemetryCollector(
            db_storage=self.db_storage,
            market_portfolio_monitor=self.market_portfolio_monitor,
            market_portfolio_stress_monte_carlo_engine=self.market_portfolio_stress_monte_carlo_engine
        )

    def test_collect_and_validate_telemetry_success(self):
        random_portfolio_id = str(uuid.uuid4())
        random_stress_level = round(random.uniform(10.0, 99.9), 2)
        random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        random_metric_value = random.randint(100, 9999)

        raw_telemetry_data = {
            "portfolio_id": random_portfolio_id,
            "stress_level": random_stress_level,
            "metrics": {
                random_metric_name: random_metric_value
            }
        }

        mock_stream = io.BytesIO(json.dumps(raw_telemetry_data).encode('utf-8'))

        with patch('skills.market_portfolio_stress_audit_telemetry_collector.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = mock_stream
            mock_response.content = json.dumps(raw_telemetry_data).encode('utf-8')
            mock_get.return_value = mock_response

            result = self.collector.collect_from_source(mock_response)

            self.assertTrue(result)
            self.db_storage.save.assert_called_once()

            saved_args = self.db_storage.save.call_args[0][0]
            self.assertEqual(saved_args["portfolio_id"], random_portfolio_id)
            self.assertEqual(saved_args["stress_level"], random_stress_level)
            self.assertEqual(saved_args["metrics"][random_metric_name], random_metric_value)

    def test_collect_telemetry_validation_error_missing_field(self):
        random_portfolio_id = str(uuid.uuid4())

        invalid_telemetry_data = {
            "portfolio_id": random_portfolio_id,
            "stress_level": None,
            "metrics": {}
        }

        with patch('skills.market_portfolio_stress_audit_telemetry_collector.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = json.dumps(invalid_telemetry_data).encode('utf-8')
            mock_get.return_value = mock_response

            with self.assertRaises(TelemetryValidationError):
                self.collector.collect_from_source(mock_response)

            self.db_storage.save.assert_not_called()

    def test_telemetry_malformed_json_raises_exception(self):
        random_garbage = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        corrupted_stream = io.BytesIO(random_garbage.encode('utf-8'))

        with patch('skills.market_portfolio_stress_audit_telemetry_collector.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = corrupted_stream.read()
            mock_get.return_value = mock_response

            with self.assertRaises((TelemetryValidationError, ValueError, json.JSONDecodeError)):
                self.collector.collect_from_source(mock_response)

    def test_telemetry_aggregation_logic(self):
        random_batch_size = random.randint(3, 10)
        random_portfolio_ids = [str(uuid.uuid4()) for _ in range(random_batch_size)]

        batch_data = [
            {
                "portfolio_id": pid,
                "stress_level": round(random.uniform(1.0, 50.0), 2),
                "metrics": {"var_loss": random.randint(1000, 50000)}
            }
            for pid in random_portfolio_ids
        ]

        stream = io.BytesIO(json.dumps(batch_data).encode('utf-8'))

        with patch('skills.market_portfolio_stress_audit_telemetry_collector.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 201
            mock_response.content = stream.read()
            mock_post.return_value = mock_response

            processed_count = self.collector.process_batch(mock_response)
            self.assertEqual(processed_count, random_batch_size)
            self.assertEqual(self.db_storage.save_batch.call_count, 1)

if __name__ == '__main__':
    unittest.main()
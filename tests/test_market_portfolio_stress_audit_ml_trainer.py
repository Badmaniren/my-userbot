import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.market_portfolio_stress_audit_ml_trainer import start_new

class TestMarketPortfolioStressAuditMlTrainer(unittest.TestCase):

    def setUp(self):
        self.random_db_path = f"sqlite:///:memory:?cache=shared_{uuid.uuid4().hex}"
        self.random_table_name = f"table_{uuid.uuid4().hex[:8]}"
        self.random_model_id = uuid.uuid4().hex
        self.random_metric_val = random.uniform(0.01, 0.99)
        self.random_payload = {
            "session_id": uuid.uuid4().hex,
            "iterations": random.randint(10, 100),
            "threshold": random.uniform(0.1, 5.0),
            "target_metric": self.random_model_id
        }

    def test_start_new_success_flow(self):
        mock_db_storage = MagicMock()
        mock_db_storage.connect.return_value = True
        mock_db_storage.fetch_historical_data.return_value = [
            {uuid.uuid4().hex: random.random() for _ in range(3)}
            for _ in range(5)
        ]

        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.evaluate.return_value = {
            "status": "ok",
            "score": self.random_metric_val
        }

        mock_ml_aggregator = MagicMock()
        mock_ml_aggregator.train_model.return_value = {
            "model_id": self.random_model_id,
            "accuracy": self.random_metric_val
        }

        with patch('skills.market_portfolio_stress_audit_ml_trainer.db_storage', mock_db_storage), \
             patch('skills.market_portfolio_stress_audit_ml_trainer.market_anomaly_detector', mock_anomaly_detector), \
             patch('skills.market_portfolio_stress_audit_ml_trainer.market_portfolio_predictive_aggregator', mock_ml_aggregator):

            result = start_new(self.random_payload)

            self.assertIsInstance(result, dict)
            self.assertIn("model_id", result)
            self.assertEqual(result["model_id"], self.random_model_id)
            mock_db_storage.connect.assert_called_once()
            mock_ml_aggregator.train_model.assert_called_once()

    def test_start_new_handles_exceptions_gracefully(self):
        mock_db_storage = MagicMock()
        random_error_msg = f"Critical DB Failure: {uuid.uuid4().hex}"
        mock_db_storage.connect.side_effect = Exception(random_error_msg)

        with patch('skills.market_portfolio_stress_audit_ml_trainer.db_storage', mock_db_storage):
            with self.assertRaises(Exception) as ctx:
                start_new(self.random_payload)
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_start_new_stream_processing_with_io(self):
        random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        mock_streamer = MagicMock()
        mock_streamer.get_stream.return_value = io.BytesIO(random_stream_data)

        mock_db_storage = MagicMock()
        mock_db_storage.save_audit_artifact.return_value = uuid.uuid4().hex

        with patch('skills.market_portfolio_stress_audit_ml_trainer.market_portfolio_stress_audit_realtime_streamer', mock_streamer), \
             patch('skills.market_portfolio_stress_audit_ml_trainer.db_storage', mock_db_storage):

            result = start_new(self.random_payload)
            self.assertIsInstance(result, dict)
            mock_streamer.get_stream.assert_called_once()

if __name__ == '__main__':
    unittest.main()
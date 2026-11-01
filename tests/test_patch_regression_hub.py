import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io

from skills.patch_regression_hub import start_new


class TestPatchRegressionHubStartNew(unittest.TestCase):

    def setUp(self):
        self.random_string_key = uuid.uuid4().hex
        self.random_string_val = uuid.uuid4().hex
        self.random_number = random.randint(1000, 99999)
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"

    def test_start_new_success_execution(self):
        dynamic_input_data = {
            self.random_string_key: self.random_string_val,
            "numeric_metric": self.random_number,
            "target": self.metric_name
        }

        mock_hub_instance = MagicMock()
        mock_hub_instance.generate_final_report.return_value = {
            "status": "verified",
            "code": self.random_string_val
        }

        with patch("skills.patch_regression_hub.AnomalyAuditHub", return_value=mock_hub_instance) as mock_hub_class:
            result = start_new(dynamic_input_data)

            mock_hub_class.assert_called_once()
            mock_hub_instance.log_anomaly.assert_called()
            mock_hub_instance.generate_final_report.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("code"), self.random_string_val)
            self.assertEqual(result.get("status"), "verified")

    def test_start_new_handles_anomalies_and_aggregates(self):
        dynamic_input_data = {
            "payload_id": uuid.uuid4().hex,
            "error_rate": random.uniform(0.1, 0.9),
            "severity_level": random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        }

        mock_hub_instance = MagicMock()
        mock_hub_instance.aggregate_and_report.return_value = {
            "aggregated": True,
            "score": dynamic_input_data["error_rate"]
        }

        with patch("skills.patch_regression_hub.AnomalyAuditHub", return_value=mock_hub_instance) as mock_hub_class:
            with patch("skills.patch_regression_hub.AnomalyLogger") as mock_logger_class:
                mock_logger_instance = mock_logger_class.return_value
                mock_logger_instance.get_anomalies.return_value = [
                    {
                        "source": dynamic_input_data["payload_id"],
                        "severity": dynamic_input_data["severity_level"]
                    }
                ]

                result = start_new(dynamic_input_data)

                self.assertIsNotNone(result)
                mock_hub_instance.aggregate_and_report.assert_called()
                mock_hub_instance.log_anomaly.assert_called()

    def test_start_new_io_stream_processing(self):
        random_byte_stream = io.BytesIO(uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=32)).encode('utf-8'))
        
        dynamic_input_data = {
            "stream_source": random_byte_stream,
            "token": uuid.uuid4().hex
        }

        mock_hub_instance = MagicMock()
        with patch("skills.patch_regression_hub.AnomalyAuditHub", return_value=mock_hub_instance):
            with patch("skills.patch_regression_hub.GitInspector") as mock_git_inspector:
                mock_git_instance = mock_git_inspector.return_value
                mock_git_instance.analyze_repository.return_value = {
                    "health_score": random.randint(0, 100),
                    "token": dynamic_input_data["token"]
                }

                result = start_new(dynamic_input_data)

                self.assertIsInstance(result, dict)
                mock_git_instance.analyze_repository.assert_called_once()

    def test_start_new_exception_handling(self):
        dynamic_input_data = {
            "fail_trigger": uuid.uuid4().hex
        }

        with patch("skills.patch_regression_hub.AnomalyAuditHub", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(Exception):
                start_new(dynamic_input_data)


if __name__ == "__main__":
    unittest.main()
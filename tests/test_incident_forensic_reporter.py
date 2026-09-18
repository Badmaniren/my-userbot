import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import json
import io

from skills.incident_forensic_reporter import start_new

class TestIncidentForensicReporterStartNew(unittest.TestCase):

    def test_start_new_success_basic(self):
        incident_id = str(uuid.uuid4())
        telemetry_source = f"/var/log/{uuid.uuid4().hex}.log"
        mock_logs = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_response_dict = {"status": uuid.uuid4().hex}

        with patch("skills.incident_forensic_reporter.incident_aggregator", return_value=mock_logs) as mock_agg, \
             patch("skills.incident_forensic_reporter.telemetry_streamer") as mock_streamer, \
             patch("skills.incident_forensic_reporter.telemetry_processor") as mock_processor, \
             patch("requests.post") as mock_post:

            mock_response = MagicMock()
            mock_response.json.return_value = expected_response_dict
            mock_post.return_value = mock_response

            result = start_new(incident_id, telemetry_source, evaluate_anomalies=False)

            mock_agg.assert_called_once()
            mock_streamer.assert_called_once_with(telemetry_source)
            mock_processor.assert_called_once_with(telemetry_source)
            
            self.assertEqual(result["status"], expected_response_dict["status"])
            self.assertEqual(result["incident_id"], incident_id)
            self.assertEqual(result["telemetry_source"], telemetry_source)
            for k, v in mock_logs.items():
                self.assertEqual(result[k], v)

            called_args, called_kwargs = mock_post.call_args
            posted_json = called_kwargs.get("json")
            self.assertEqual(posted_json["incident_id"], incident_id)
            self.assertEqual(posted_json["telemetry_source"], telemetry_source)
            for k, v in mock_logs.items():
                self.assertEqual(posted_json[k], v)

    def test_start_new_with_anomalies(self):
        incident_id = str(uuid.uuid4())
        telemetry_source = f"/tmp/{uuid.uuid4().hex}.dat"
        mock_logs = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_anomaly_score = round(random.uniform(0.1, 99.9), 2)
        expected_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        expected_response_dict = {"acknowledged": True}

        with patch("skills.incident_forensic_reporter.incident_aggregator", return_value=mock_logs), \
             patch("skills.incident_forensic_reporter.telemetry_streamer"), \
             patch("skills.incident_forensic_reporter.telemetry_processor"), \
             patch("skills.incident_forensic_reporter.telemetry_anomaly_evaluator_core", return_value={"anomaly_score": expected_anomaly_score}) as mock_anomaly, \
             patch("skills.incident_forensic_reporter.incident_severity_evaluator", return_value=expected_severity) as mock_severity, \
             patch("requests.post") as mock_post:

            mock_response = MagicMock()
            mock_response.json.return_value = expected_response_dict
            mock_post.return_value = mock_response

            result = start_new(incident_id, telemetry_source, evaluate_anomalies=True)

            mock_anomaly.assert_called_once()
            mock_severity.assert_called_once()

            self.assertEqual(result["anomaly_score"], expected_anomaly_score)
            self.assertEqual(result["severity"], expected_severity)
            self.assertEqual(result["incident_id"], incident_id)

    def test_start_new_streamer_file_not_found(self):
        incident_id = str(uuid.uuid4())
        telemetry_source = f"/nonexistent/{uuid.uuid4().hex}"

        with patch("skills.incident_forensic_reporter.incident_aggregator", return_value={}), \
             patch("skills.incident_forensic_reporter.telemetry_streamer", side_effect=FileNotFoundError):

            with self.assertRaises(FileNotFoundError):
                start_new(incident_id, telemetry_source, evaluate_anomalies=False)

    def test_start_new_processor_exception(self):
        incident_id = str(uuid.uuid4())
        telemetry_source = f"/corrupted/{uuid.uuid4().hex}"
        custom_exception = RuntimeError(uuid.uuid4().hex)

        with patch("skills.incident_forensic_reporter.incident_aggregator", return_value={}), \
             patch("skills.incident_forensic_reporter.telemetry_streamer"), \
             patch("skills.incident_forensic_reporter.telemetry_processor", side_effect=custom_exception):

            with self.assertRaises(RuntimeError) as ctx:
                start_new(incident_id, telemetry_source, evaluate_anomalies=False)
            
            self.assertEqual(str(ctx.exception), str(custom_exception))
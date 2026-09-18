import unittest
from unittest.mock import patch
import io
import uuid
import random
import string
from skills.incident_forensic_summarizer import start_net, start_new

class TestIncidentForensicSummarizerInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_incident_id = f"inc-{uuid.uuid4().hex}"
        self.random_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        self.random_faulty_param = f"fault-{uuid.uuid4().hex}"

    def test_start_new_execution_flow_and_data_integrity(self):
        mock_payload = {
            "incident_id": self.random_incident_id,
            "telemetry_payload": {"raw": self.random_stream_data.decode('utf-8')},
            "severity_level": "CRITICAL"
        }

        with patch('skills.incident_forensic_summarizer.incident_aggregator', return_value=mock_payload) as mock_aggregator, \
             patch('skills.incident_forensic_summarizer.incident_forensic_summarizer') as mock_summarizer:

            mock_summarizer.return_value = {
                "summary_id": f"sum-{uuid.uuid4().hex}",
                "target_incident_id": self.random_incident_id,
                "telemetry_dump": str(mock_payload["telemetry_payload"]),
                "report_file_path": f"report_sum-{uuid.uuid4().hex}.txt"
            }

            stream_obj = io.BytesIO(self.random_stream_data)
            result = start_new(self.random_incident_id, stream_obj)

            mock_aggregator.assert_called_once()
            mock_summarizer.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["target_incident_id"], self.random_incident_id)
            self.assertIn("summary_id", result)
            self.assertIn("report_file_path", result)

    def test_start_new_exception_handling_inquisitorial(self):
        with patch('skills.incident_forensic_summarizer.incident_severity_evaluator.evaluate', side_effect=ValueError("Inquisitorial Chaos Error")) as mock_eval:
            with self.assertRaises((ValueError, Exception)):
                start_new(faulty_param=self.random_faulty_param)
            mock_eval.assert_called_once_with(self.random_faulty_param)

    def test_start_new_with_kwargs_and_telemetry_source(self):
        stream_obj = io.BytesIO(self.random_stream_data)
        mock_payload = {
            "incident_id": self.random_incident_id,
            "telemetry_payload": {"raw": self.random_stream_data.decode('utf-8')},
            "severity_level": "CRITICAL"
        }

        with patch('skills.incident_forensic_summarizer.incident_aggregator', return_value=mock_payload) as mock_aggregator, \
             patch('skills.incident_forensic_summarizer.incident_forensic_summarizer') as mock_summarizer:

            mock_summarizer.return_value = {
                "summary_id": f"sum-{uuid.uuid4().hex}",
                "target_incident_id": self.random_incident_id,
                "telemetry_dump": str(mock_payload["telemetry_payload"]),
                "report_file_path": f"report_sum-{uuid.uuid4().hex}.txt"
            }

            result = start_new(incident_id=self.random_incident_id, telemetry_source=stream_obj)

            mock_aggregator.assert_called_once()
            self.assertEqual(result["target_incident_id"], self.random_incident_id)

    def test_start_new_without_args_generates_random_id(self):
        mock_payload = {
            "incident_id": f"INC-{uuid.uuid4().hex}",
            "telemetry_payload": {},
            "severity_level": "CRITICAL"
        }

        with patch('skills.incident_forensic_summarizer.incident_aggregator', return_value=mock_payload) as mock_aggregator, \
             patch('skills.incident_forensic_summarizer.incident_forensic_summarizer') as mock_summarizer:

            mock_summarizer.return_value = {
                "summary_id": f"sum-{uuid.uuid4().hex}",
                "target_incident_id": mock_payload["incident_id"],
                "telemetry_dump": "",
                "report_file_path": f"report_sum-{uuid.uuid4().hex}.txt"
            }

            result = start_new()

            mock_aggregator.assert_called_once()
            self.assertIn("target_incident_id", result)
            self.assertTrue(result["target_incident_id"])

if __name__ == '__main__':
    unittest.main()
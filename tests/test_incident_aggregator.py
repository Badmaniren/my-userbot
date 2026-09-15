import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_aggregator import aggregate_incidents


class TestIncidentAggregator(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.incident_id = uuid.uuid4().hex
        self.error_message = f"error_{uuid.uuid4().hex[:6]}"
        self.traceback_str = f"Traceback (most recent call last):\n  File \"{uuid.uuid4().hex}.py\", line {random.randint(1, 100)}, in <module>\n    raise Exception(\"{self.error_message}\")"
        self.metrics_payload = {
            "incident_id": self.incident_id,
            "module_name": self.module_name,
            "success": random.choice([True, False]),
            "metric_value": random.random()
        }

    def test_aggregate_incidents_success_flow(self):
        with patch('skills.incident_aggregator.ErrorRecoveryHub') as mock_hub_cls, \
             patch('skills.incident_aggregator.PatchMetricCollector') as mock_collector_cls:

            mock_hub = mock_hub_cls.return_value
            mock_collector = mock_collector_cls.return_value

            mock_hub.capture_failure.return_value = self.incident_id
            mock_hub.analyze_failure.return_value = {
                "incident_id": self.incident_id,
                "status": "analyzed",
                "details": self.error_message
            }
            mock_collector.record_metric.return_value = self.metrics_payload
            mock_collector.get_metrics_summary.return_value = f"Summary for {self.module_name}"

            result = aggregate_incidents(
                module_name=self.module_name,
                exception=Exception(self.error_message),
                traceback_str=self.traceback_str
            )

            mock_hub.capture_failure.assert_called_once_with(
                self.module_name, 
                unittest.mock.ANY, 
                self.traceback_str
            )
            mock_hub.analyze_failure.assert_called_once_with(self.incident_id)
            mock_collector.record_metric.assert_called_once()
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("module_name"), self.module_name)
            self.assertIn("metrics_summary", result)

    def test_aggregate_incidents_empty_traceback(self):
        custom_exception = RuntimeError(f"err_{uuid.uuid4().hex}")
        with patch('skills.incident_aggregator.ErrorRecoveryHub') as mock_hub_cls, \
             patch('skills.incident_aggregator.PatchMetricCollector') as mock_collector_cls:

            mock_hub = mock_hub_cls.return_value
            mock_collector = mock_collector_cls.return_value

            mock_hub.capture_failure.return_value = self.incident_id
            mock_hub.analyze_failure.return_value = {"status": "failed"}

            result = aggregate_incidents(
                module_name=self.module_name,
                exception=custom_exception,
                traceback_str=""
            )

            mock_hub.capture_failure.assert_called_once()
            self.assertIsNotNone(result)
            self.assertEqual(result["incident_id"], self.incident_id)

    def test_aggregate_incidents_stream_processing(self):
        stream_data = io.BytesIO(f"stream_content_{uuid.uuid4().hex}".encode('utf-8'))
        
        with patch('skills.incident_aggregator.ErrorRecoveryHub') as mock_hub_cls, \
             patch('skills.incident_aggregator.PatchMetricCollector') as mock_collector_cls:

            mock_hub = mock_hub_cls.return_value
            mock_collector = mock_collector_cls.return_value

            mock_hub.analyze_and_recover.return_value = {
                "recovered": True,
                "incident_id": self.incident_id
            }

            from skills.incident_aggregator import process_incident_stream
            
            outcome = process_incident_stream(self.module_name, stream_data)

            mock_hub.analyze_and_recover.assert_called_once()
            self.assertTrue(outcome.get("recovered"))
            self.assertEqual(outcome.get("incident_id"), self.incident_id)

    def test_aggregate_incidents_export_analytics(self):
        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        export_format = random.choice(["json", "csv", "xml"])

        with patch('skills.incident_aggregator.ErrorRecoveryHub') as mock_hub_cls, \
             patch('skills.incident_aggregator.PatchMetricCollector') as mock_collector_cls:

            mock_collector = mock_collector_cls.return_value
            mock_collector.export_metrics.return_value = True

            from skills.incident_aggregator import export_incident_analytics
            
            success = export_incident_analytics(
                module_name=self.module_name, 
                output_path=output_path, 
                format=export_format
            )

            mock_collector.export_metrics.assert_called_once_with(output_path, export_format)
            self.assertTrue(success)
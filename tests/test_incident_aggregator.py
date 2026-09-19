import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
from skills.incident_aggregator import (
    IncidentAggregator,
    aggregate_incidents,
    process_incident_stream,
    export_incident_analytics
)

class TestIncidentAggregator(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"Err_{uuid.uuid4().hex[:6]}"
        self.traceback_str = f"Traceback at {uuid.uuid4().hex}"
        self.incident_id = f"inc_{uuid.uuid4().hex}"
        self.output_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.format_type = random.choice(["json", "csv", "xml"])

    def test_incident_aggregator_class_process_new(self):
        rand_summary = {uuid.uuid4().hex: random.randint(1, 100)}
        rand_analysis = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_payload = {uuid.uuid4().hex: random.random()}
        rand_history = [uuid.uuid4().hex, uuid.uuid4().hex]

        with patch('skills.incident_aggregator.ErrorRecoveryHub') as MockHub, \
             patch('skills.incident_aggregator.PatchMetricCollector') as MockCol:

            hub_instance = MockHub.return_value
            hub_instance.capture_failure.return_value = self.incident_id
            hub_instance.analyze_failure.return_value = rand_analysis
            hub_instance.get_incident_history.return_value = rand_history

            col_instance = MockCol.return_value
            col_instance.record_metric.return_value = rand_payload
            col_instance.get_metrics_summary.return_value = rand_summary

            aggregator = IncidentAggregator()
            result = aggregator.process_and_aggregate(
                self.module_name, 
                Exception(self.exception_msg), 
                self.traceback_str
            )

            hub_instance.capture_failure.assert_called_once_with(
                self.module_name, 
                Exception(self.exception_msg), 
                self.traceback_str
            )
            col_instance.record_metric.assert_called_once()
            
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["module_name"], self.module_name)
            self.assertEqual(result["analysis"], rand_analysis)
            self.assertEqual(result["metrics"], rand_payload)
            self.assertEqual(result["metrics_summary"], rand_summary)
            self.assertEqual(result["history"], rand_history)

    def test_incident_aggregator_class_process_existing_id(self):
        rand_summary = {uuid.uuid4().hex: random.randint(1, 50)}
        rand_payload = {uuid.uuid4().hex: random.random()}

        with patch('skills.incident_aggregator.ErrorRecoveryHub') as MockHub, \
             patch('skills.incident_aggregator.PatchMetricCollector') as MockCol:

            hub_instance = MockHub.return_value
            hub_instance.analyze_failure.return_value = {}
            hub_instance.get_incident_history.return_value = []

            col_instance = MockCol.return_value
            col_instance.record_metric.return_value = rand_payload
            col_instance.get_metrics_summary.return_value = rand_summary

            aggregator = IncidentAggregator()
            result = aggregator.process_and_aggregate(
                self.module_name, 
                Exception(self.exception_msg), 
                self.traceback_str, 
                incident_id=self.incident_id
            )

            hub_instance.capture_failure.assert_not_called()
            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["module_name"], self.module_name)

    def test_aggregate_incidents_function(self):
        rand_summary = {uuid.uuid4().hex: random.randint(10, 20)}
        rand_analysis_key = uuid.uuid4().hex
        rand_analysis_val = uuid.uuid4().hex
        rand_analysis = {rand_analysis_key: rand_analysis_val}
        rand_payload = {uuid.uuid4().hex: random.random()}

        with patch('skills.incident_aggregator.ErrorRecoveryHub') as MockHub, \
             patch('skills.incident_aggregator.PatchMetricCollector') as MockCol:

            hub_instance = MockHub.return_value
            hub_instance.capture_failure.return_value = self.incident_id
            hub_instance.analyze_failure.return_value = rand_analysis

            col_instance = MockCol.return_value
            col_instance.record_metric.return_value = rand_payload
            col_instance.get_metrics_summary.return_value = rand_summary

            result = aggregate_incidents(
                self.module_name, 
                Exception(self.exception_msg), 
                self.traceback_str
            )

            self.assertEqual(result["incident_id"], self.incident_id)
            self.assertEqual(result["module_name"], self.module_name)
            self.assertEqual(result["metrics_summary"], rand_summary)
            self.assertEqual(result.get(rand_analysis_key), rand_analysis_val)

    def test_process_incident_stream_with_recovery(self):
        stream_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_response = {"recovered": True, "details": uuid.uuid4().hex}

        with patch('skills.incident_aggregator.ErrorRecoveryHub') as MockHub:
            hub_instance = MockHub.return_value
            hub_instance.analyze_and_recover.return_value = expected_response

            result = process_incident_stream(self.module_name, stream_payload)

            hub_instance.analyze_and_recover.assert_called_once_with(self.module_name, stream_payload)
            self.assertEqual(result, expected_response)

    def test_process_incident_stream_without_recovery(self):
        stream_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.incident_aggregator.ErrorRecoveryHub') as MockHub:
            hub_instance = MockHub.return_value
            del hub_instance.analyze_and_recover

            result = process_incident_stream(self.module_name, stream_payload)

            self.assertEqual(result, {"recovered": False})

    def test_export_incident_analytics_with_export(self):
        expected_export_result = random.choice([True, False])

        with patch('skills.incident_aggregator.PatchMetricCollector') as MockCol:
            col_instance = MockCol.return_value
            col_instance.export_metrics.return_value = expected_export_result

            result = export_incident_analytics(self.module_name, self.output_path, format=self.format_type)

            col_instance.export_metrics.assert_called_once_with(self.output_path, self.format_type)
            self.assertEqual(result, expected_export_result)

    def test_export_incident_analytics_without_export(self):
        with patch('skills.incident_aggregator.PatchMetricCollector') as MockCol:
            col_instance = MockCol.return_value
            del col_instance.export_metrics

            result = export_incident_analytics(self.module_name, self.output_path, format=self.format_type)

            self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.system_health_aggregator import SystemHealthAggregator, aggregate_system_health


class TestSystemHealthAggregator(unittest.TestCase):

    def setUp(self):
        self.module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.exception_msg = f"err_{uuid.uuid4().hex[:8]}"
        self.traceback_str = f"Traceback at line {random.randint(1, 100)}"
        self.incident_id = str(random.randint(1000, 9999))
        self.audit_summary = f"audit_{uuid.uuid4().hex[:8]}"
        self.metrics = {"cpu_usage": random.randint(10, 99), "memory": random.randint(100, 1024)}
        self.export_path = f"/tmp/{uuid.uuid4().hex}.json"

    @patch("skills.system_health_aggregator.IncidentAggregator")
    @patch("skills.system_health_aggregator.SystemHealthReporter")
    def test_handle_stream_report(self, mock_reporter_cls, mock_aggregator_cls):
        mock_reporter = mock_reporter_cls.return_value
        expected_stream_data = {"stream_id": uuid.uuid4().hex}
        mock_reporter.parse_stream_data.return_value = expected_stream_data

        aggregator = SystemHealthAggregator()
        stream = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))
        result = aggregator.handle_stream_report(stream)

        mock_reporter.parse_stream_data.assert_called_once_with(stream)
        self.assertEqual(result, expected_stream_data)

    @patch("skills.system_health_aggregator.IncidentAggregator")
    @patch("skills.system_health_aggregator.SystemHealthReporter")
    def test_export_current_health(self, mock_reporter_cls, mock_aggregator_cls):
        mock_reporter = mock_reporter_cls.return_value
        mock_reporter.export_health_report.return_value = True

        aggregator = SystemHealthAggregator()
        parsed_data = {"status": uuid.uuid4().hex}
        result = aggregator.export_current_health(parsed_data, self.export_path)

        mock_reporter.export_health_report.assert_called_once_with(parsed_data, self.export_path)
        self.assertTrue(result)

    @patch("skills.system_health_aggregator.IncidentAggregator")
    @patch("skills.system_health_aggregator.SystemHealthReporter")
    def test_compile_metrics(self, mock_reporter_cls, mock_aggregator_cls):
        mock_reporter = mock_reporter_cls.return_value
        incidents_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        patches_list = [uuid.uuid4().hex]
        compiled_result = {"aggregated": random.randint(1, 100)}
        mock_reporter.aggregate_system_metrics.return_value = compiled_result

        aggregator = SystemHealthAggregator()
        result = aggregator.compile_metrics(incidents_list, patches_list)

        mock_reporter.aggregate_system_metrics.assert_called_once_with(incidents_list, patches_list)
        self.assertEqual(result, compiled_result)

    @patch("skills.system_health_aggregator.IncidentAggregator")
    @patch("skills.system_health_aggregator.SystemHealthReporter")
    def test_collect_and_aggregate_health(self, mock_reporter_cls, mock_aggregator_cls):
        mock_reporter = mock_reporter_cls.return_value
        mock_aggregator = mock_aggregator_cls.return_value

        incident_output = {"detail": uuid.uuid4().hex}
        mock_aggregator.process_and_aggregate.return_value = incident_output

        health_output = {"status": "ok", "metrics": "invalid_string_or_missing"}
        mock_reporter.generate_health_report.return_value = health_output

        aggregator = SystemHealthAggregator()
        result = aggregator.collect_and_aggregate_health(
            self.module_name,
            self.exception_msg,
            self.traceback_str,
            self.incident_id,
            self.audit_summary,
            self.metrics
        )

        mock_aggregator.process_and_aggregate.assert_called_once()
        args, _ = mock_aggregator.process_and_aggregate.call_args
        self.assertEqual(args[0], self.module_name)
        self.assertIsInstance(args[1], Exception)
        self.assertEqual(str(args[1]), self.exception_msg)
        self.assertEqual(args[2], self.traceback_str)
        self.assertEqual(args[3], self.incident_id)

        mock_reporter.generate_health_report.assert_called_once()

        self.assertIn("incident_aggregation", result)
        self.assertIn("health_report", result)
        self.assertEqual(result["incident_aggregation"]["incident_id"], self.incident_id)
        self.assertEqual(result["incident_aggregation"]["module_name"], self.module_name)
        self.assertEqual(result["health_report"]["metrics"], self.metrics)

    @patch("skills.system_health_aggregator.IncidentAggregator")
    @patch("skills.system_health_aggregator.SystemHealthReporter")
    def test_export_aggregated_health(self, mock_reporter_cls, mock_aggregator_cls):
        mock_reporter = mock_reporter_cls.return_value
        mock_reporter.export_health_report.return_value = True

        aggregator = SystemHealthAggregator()
        report = {"health": uuid.uuid4().hex}
        result = aggregator.export_aggregated_health(report, self.export_path)

        mock_reporter.export_health_report.assert_called_once_with(report, self.export_path)
        self.assertTrue(result)

    @patch("skills.system_health_aggregator.IncidentAggregator")
    @patch("skills.system_health_aggregator.SystemHealthReporter")
    def test_aggregate_system_health_function(self, mock_reporter_cls, mock_aggregator_cls):
        mock_reporter = mock_reporter_cls.return_value
        mock_aggregator = mock_aggregator_cls.return_value

        incident_output = {"status": uuid.uuid4().hex}
        mock_aggregator.process_and_aggregate.return_value = incident_output

        health_output = {"report_id": uuid.uuid4().hex}
        mock_reporter.generate_health_report.return_value = health_output

        exception_obj = Exception(self.exception_msg)
        result = aggregate_system_health(
            self.module_name,
            exception_obj,
            self.traceback_str,
            self.incident_id,
            self.audit_summary,
            self.metrics
        )

        mock_aggregator.process_and_aggregate.assert_called_once_with(
            self.module_name,
            exception_obj,
            self.traceback_str,
            self.incident_id
        )

        mock_reporter.generate_health_report.assert_called_once_with(
            module_name=self.module_name,
            incident_data=incident_output,
            audit_summary=self.audit_summary,
            metrics=self.metrics
        )

        self.assertIn("health_report", result)
        self.assertIn("incident_summary", result)
        self.assertEqual(result["health_report"]["metrics"], self.metrics)
        self.assertEqual(result["incident_summary"], incident_output)


if __name__ == "__main__":
    unittest.main()
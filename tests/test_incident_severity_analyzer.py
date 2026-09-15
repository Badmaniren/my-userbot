import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.incident_severity_analyzer import start_new


class TestIncidentSeverityAnalyzerArchitectInquisitor(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex
        self.random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self.random_int = random.randint(100, 99999)
        self.random_float = random.uniform(1.0, 100.0)
        self.random_uuid = str(uuid.uuid4())

        self.mock_components = {
            "auto_patch_pipeline": f"pipeline_{self.random_prefix}",
            "dependency_audit_reporter": f"reporter_{self.random_prefix}",
            "error_recovery_hub": f"hub_{self.random_prefix}",
            "incident_aggregator": f"aggregator_{self.random_prefix}",
            "incident_trend_analyzer": f"analyzer_{self.random_prefix}",
            "incident_trend_forecaster": f"forecaster_{self.random_prefix}",
            "notification_channel_dispatcher": f"dispatcher_{self.random_prefix}",
            "notification_template_engine": f"engine_{self.random_prefix}",
            "notification_webhook_broadcaster": f"broadcaster_{self.random_prefix}",
            "package_requirement_reader": f"reader_{self.random_prefix}",
            "patch_auto_executor": f"executor_{self.random_prefix}",
            "patch_metric_collector": f"collector_{self.random_prefix}",
            "patch_scheduler": f"scheduler_{self.random_prefix}",
            "patch_validator": f"validator_{self.random_prefix}",
            "preventive_patch_applier": f"applier_{self.random_prefix}",
            "pypi_client": f"client_{self.random_prefix}",
            "recovery_dashboard_generator": f"dashboard_{self.random_prefix}",
            "recovery_report_exporter": f"exporter_{self.random_prefix}",
            "system_health_aggregator": f"health_agg_{self.random_prefix}",
            "system_health_audit_pipeline": f"health_pipe_{self.random_prefix}",
            "system_health_monitoring_gateway": f"gateway_{self.random_prefix}",
            "system_health_reporter": f"health_rep_{self.random_prefix}",
            "system_health_telemetry_collector": f"telemetry_{self.random_prefix}",
            "vulnerability_scanner": f"scanner_{self.random_prefix}"
        }

    def test_start_new_initialization_flow(self):
        dynamic_payload = {
            "uuid": self.random_uuid,
            "metric": self.random_float,
            "token": self.random_string,
            "components": self.mock_components
        }

        with patch("skills.incident_severity_analyzer.system_health_telemetry_collector") as mock_telemetry:
            mock_telemetry.collect.return_value = io.BytesIO(f"telemetry_data_{self.random_string}".encode('utf-8'))

            result = start_new(dynamic_payload)

            self.assertIsNotNone(result)
            if isinstance(result, dict):
                self.assertIn(self.random_uuid, str(result.values()))

    def test_start_new_exception_handling(self):
        failing_payload = {
            "error_code": self.random_int,
            "error_msg": f"crit_err_{self.random_string}"
        }

        with patch("skills.incident_severity_analyzer.incident_aggregator") as mock_aggregator:
            mock_aggregator.side_effect = RuntimeError(f"Failure_{self.random_uuid}")

            with self.assertRaises(Exception) as context:
                start_new(failing_payload)

            self.assertIn(self.random_uuid, str(context.exception))

    def test_start_new_data_integrity_check(self):
        unique_marker = uuid.uuid4().hex
        custom_payload = {
            "marker": unique_marker,
            "severity_level": self.random_int,
            "target": self.random_string
        }

        with patch("skills.incident_severity_analyzer.system_health_monitoring_gateway") as mock_gateway:
            mock_response = MagicMock()
            mock_response.read.return_value = io.BytesIO(f"payload_processed_{unique_marker}".encode('utf-8')).read()
            mock_gateway.process.return_value = mock_response

            res = start_new(custom_payload)

            mock_gateway.process.assert_called_once()
            call_args = str(mock_gateway.process.call_args)
            self.assertIn(unique_marker, call_args)


if __name__ == "__main__":
    unittest.main()
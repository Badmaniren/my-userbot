import json
import random
import string
import unittest
import uuid
from unittest.mock import MagicMock, mock_open, patch

from skills.anomaly_audit_exporter import (
    AnomalyAuditExporter,
    AnomalyAuditExporterError,
)


def _rnd_str(length: int = 10) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _rnd_path() -> str:
    return f"/{_rnd_str(6)}/{uuid.uuid4().hex}/{_rnd_str(8)}.log"


class TestAnomalyAuditExporterUnit(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_path = f"/var/repo/{uuid.uuid4().hex}"
        self.log_path = _rnd_path()
        self.threshold = round(random.uniform(0.01, 100.0), 4)

    def test_init_instantiates_hub_and_logger(self) -> None:
        hub_patch_target = "skills.anomaly_audit_exporter.AnomalyAuditHub"
        logger_patch_target = "skills.anomaly_audit_exporter.AnomalyLogger"

        with patch(hub_patch_target) as mock_hub_cls, patch(logger_patch_target) as mock_logger_cls:
            dummy_hub = MagicMock()
            dummy_logger = MagicMock()
            mock_hub_cls.return_value = dummy_hub
            mock_logger_cls.return_value = dummy_logger

            exporter = AnomalyAuditExporter(
                repo_path=self.repo_path,
                log_path=self.log_path,
                threshold=self.threshold,
            )

            self.assertEqual(exporter.repo_path, self.repo_path)
            self.assertEqual(exporter.log_path, self.log_path)
            self.assertEqual(exporter.threshold, self.threshold)

            mock_hub_cls.assert_called_once_with(self.repo_path, self.log_path, self.threshold)
            mock_logger_cls.assert_called_once_with(self.log_path)
            self.assertIs(exporter.hub, dummy_hub)
            self.assertIs(exporter.logger, dummy_logger)

    def test_log_anomaly_success(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            source = f"service-{uuid.uuid4().hex[:8]}"
            severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
            details = {uuid.uuid4().hex: _rnd_str(12), "code": random.randint(100, 999)}
            telemetry = {uuid.uuid4().hex: random.random(), "ts": _rnd_str(15)}

            exporter.log_anomaly(source, severity, details, telemetry)

            exporter.hub.log_anomaly.assert_called_once_with(source, severity, details, telemetry)
            exporter.logger.log_anomaly.assert_called_once_with(source, severity, details, telemetry)

    def test_log_anomaly_none_telemetry_snapshot(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            source = f"source-{_rnd_str(5)}"
            severity = "WARN"
            details = {"payload": uuid.uuid4().hex}

            exporter.log_anomaly(source, severity, details, None)

            exporter.hub.log_anomaly.assert_called_once_with(source, severity, details, None)
            exporter.logger.log_anomaly.assert_called_once_with(source, severity, details, None)

    def test_log_anomaly_hub_failure_raises_exporter_error(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            err_msg = f"Hub failure {uuid.uuid4().hex}"
            exporter.hub.log_anomaly.side_effect = RuntimeError(err_msg)

            with self.assertRaises(AnomalyAuditExporterError) as ctx:
                exporter.log_anomaly("agent", "HIGH", {"detail": _rnd_str()})

            self.assertIn(err_msg, str(ctx.exception))
            self.assertIsInstance(ctx.exception.__cause__, RuntimeError)
            exporter.logger.log_anomaly.assert_not_called()

    def test_log_anomaly_logger_failure_raises_exporter_error(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            err_msg = f"Logger failure {uuid.uuid4().hex}"
            exporter.logger.log_anomaly.side_effect = OSError(err_msg)

            with self.assertRaises(AnomalyAuditExporterError) as ctx:
                exporter.log_anomaly("agent", "CRITICAL", {"detail": _rnd_str()})

            self.assertIn(err_msg, str(ctx.exception))
            self.assertIsInstance(ctx.exception.__cause__, OSError)

    def test_aggregate_and_report_success(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()

            metric_name = f"latency_{uuid.uuid4().hex[:6]}"
            metric_val = round(random.uniform(10.0, 500.0), 3)
            expected_report = {
                "metric": metric_name,
                "score": metric_val,
                "token": uuid.uuid4().hex,
            }
            exporter.hub.aggregate_and_report.return_value = expected_report

            result = exporter.aggregate_and_report(metric_name, metric_val)

            self.assertEqual(result, expected_report)
            exporter.hub.aggregate_and_report.assert_called_once_with(metric_name, metric_val)

    def test_aggregate_and_report_attribute_error_wrapped(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()

            err_msg = f"'{_rnd_str()}' object has no attribute 'get'"
            exporter.hub.aggregate_and_report.side_effect = AttributeError(err_msg)

            metric_name = f"cpu_{uuid.uuid4().hex[:4]}"
            metric_val = random.uniform(1.0, 99.0)

            with self.assertRaises(AnomalyAuditExporterError) as ctx:
                exporter.aggregate_and_report(metric_name, metric_val)

            self.assertIn(err_msg, str(ctx.exception))
            self.assertIsInstance(ctx.exception.__cause__, AttributeError)

    def test_export_report_without_output_path(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            mock_hub_report = {
                "hub_id": uuid.uuid4().hex,
                "anomalies_count": random.randint(1, 20),
            }
            mock_logger_report = {
                "logger_id": uuid.uuid4().hex,
                "status": "success",
            }

            exporter.hub.generate_final_report.return_value = mock_hub_report
            exporter.logger.get_structured_report.return_value = mock_logger_report

            result = exporter.export_report()

            exporter.hub.generate_final_report.assert_called_once()
            exporter.logger.get_structured_report.assert_called_once()

            self.assertEqual(result["hub_report"], mock_hub_report)
            self.assertEqual(result["logger_report"], mock_logger_report)

    def test_export_report_with_output_path_writes_json(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            mock_hub_data = {"token": uuid.uuid4().hex, "count": random.randint(10, 50)}
            mock_logger_data = {"entries": [uuid.uuid4().hex, _rnd_str(10)]}
            exporter.hub.generate_final_report.return_value = mock_hub_data
            exporter.logger.get_structured_report.return_value = mock_logger_data

            target_out_path = f"/tmp/export_{uuid.uuid4().hex}.json"

            m_open = mock_open()
            with patch("builtins.open", m_open):
                result = exporter.export_report(output_path=target_out_path)

            m_open.assert_called_once_with(target_out_path, "w", encoding="utf-8")
            handle = m_open()

            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_written = json.loads(written_content)

            self.assertEqual(result, parsed_written)
            self.assertEqual(parsed_written["hub_report"], mock_hub_data)
            self.assertEqual(parsed_written["logger_report"], mock_logger_data)

    def test_export_report_io_error_raises_anomaly_audit_exporter_error(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            exporter.hub.generate_final_report.return_value = {}
            exporter.logger.get_structured_report.return_value = {}

            target_out_path = f"/restricted_{uuid.uuid4().hex}/output.json"
            err_msg = f"Disk full {uuid.uuid4().hex}"

            with patch("builtins.open", side_effect=IOError(err_msg)):
                with self.assertRaises(AnomalyAuditExporterError) as ctx:
                    exporter.export_report(output_path=target_out_path)

                self.assertIn(err_msg, str(ctx.exception))
                self.assertIsInstance(ctx.exception.__cause__, IOError)

    def test_export_report_hub_failure_raises_exporter_error(self) -> None:
        with patch("skills.anomaly_audit_exporter.AnomalyAuditHub"), \
             patch("skills.anomaly_audit_exporter.AnomalyLogger"):
            exporter = AnomalyAuditExporter(self.repo_path, self.log_path, self.threshold)
            exporter.hub = MagicMock()
            exporter.logger = MagicMock()

            err_msg = f"Final report failure {uuid.uuid4().hex}"
            exporter.hub.generate_final_report.side_effect = RuntimeError(err_msg)

            with self.assertRaises(AnomalyAuditExporterError) as ctx:
                exporter.export_report()

            self.assertIn(err_msg, str(ctx.exception))
            self.assertIsInstance(ctx.exception.__cause__, RuntimeError)
            exporter.logger.get_structured_report.assert_not_called()


if __name__ == "__main__":
    unittest.main()
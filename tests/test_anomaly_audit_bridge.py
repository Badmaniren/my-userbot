import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import uuid
import random
import string
import io

from skills.anomaly_audit_bridge import AnomalyAuditBridge, AnomalyAuditBridgeError
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyAuditBridge(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.repo_path = f"/tmp/repo_{self.rand_suffix}"
        self.log_path = f"/tmp/log_{self.rand_suffix}.log"
        self.threshold = random.uniform(0.1, 0.9)
        self.output_path = f"/tmp/output_{self.rand_suffix}.json"
        self.html_output_path = f"/tmp/output_{self.rand_suffix}.html"
        self.stream_id = f"stream_{self.rand_suffix}"

        self.source = f"source_{self.rand_suffix}"
        self.severity = random.choice(["INFO", "WARNING", "CRITICAL"])
        self.details = f"details_{uuid.uuid4().hex}"
        self.telemetry = {"cpu": random.randint(10, 99), "mem": random.randint(20, 80)}

        self.metric_name = f"metric_{self.rand_suffix}"
        self.metric_value = random.uniform(1.0, 100.0)

    def test_init_with_audit_hub_instance(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        mock_exporter = MagicMock()

        bridge = AnomalyAuditBridge(repo_path_or_hub=mock_hub, digest_exporter=mock_exporter)
        self.assertEqual(bridge.audit_hub, mock_hub)
        self.assertEqual(bridge.digest_exporter, mock_exporter)

    def test_init_with_explicit_audit_hub_kwarg(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        mock_exporter = MagicMock()

        bridge = AnomalyAuditBridge(audit_hub=mock_hub, digest_exporter=mock_exporter)
        self.assertEqual(bridge.audit_hub, mock_hub)
        self.assertEqual(bridge.digest_exporter, mock_exporter)

    @patch("skills.anomaly_audit_bridge.AnomalyAuditHub")
    @patch("skills.anomaly_audit_bridge.DigestExporter")
    def test_init_creates_default_hub_and_exporter(self, mock_digest_cls, mock_hub_cls):
        instance_hub = mock_hub_cls.return_value
        instance_exporter = mock_digest_cls.return_value

        bridge = AnomalyAuditBridge(self.repo_path, self.log_path, self.threshold)

        mock_hub_cls.assert_called_once_with(self.repo_path, self.log_path, self.threshold)
        mock_digest_cls.assert_called_once()
        self.assertEqual(bridge.audit_hub, instance_hub)
        self.assertEqual(bridge.digest_exporter, instance_exporter)

    def test_init_raises_bridge_error_on_failure(self):
        with patch("skills.anomaly_audit_bridge.AnomalyAuditHub", side_effect=Exception(f"fail_{self.rand_suffix}")):
            with self.assertRaises(AnomalyAuditBridgeError) as ctx:
                AnomalyAuditBridge(self.repo_path, self.log_path, self.threshold)
            self.assertIn(f"fail_{self.rand_suffix}", str(ctx.exception))

    def test_log_anomaly_delegation(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        expected_result = f"logged_{uuid.uuid4().hex}"
        mock_hub.log_anomaly.return_value = expected_result

        bridge = AnomalyAuditBridge(audit_hub=mock_hub)
        res = bridge.log_anomaly(self.source, self.severity, self.details, self.telemetry)

        mock_hub.log_anomaly.assert_called_once_with(self.source, self.severity, self.details, self.telemetry)
        self.assertEqual(res, expected_result)

    def test_log_anomaly_exception_handling(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        mock_hub.log_anomaly.side_effect = Exception(f"error_log_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=mock_hub)
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.log_anomaly(self.source, self.severity, self.details, self.telemetry)
        self.assertIn(f"error_log_{self.rand_suffix}", str(ctx.exception))

    def test_aggregate_and_report_delegation(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        expected_result = random.randint(1, 1000)
        mock_hub.aggregate_and_report.return_value = expected_result

        bridge = AnomalyAuditBridge(audit_hub=mock_hub)
        res = bridge.aggregate_and_report(self.metric_name, self.metric_value)

        mock_hub.aggregate_and_report.assert_called_once_with(self.metric_name, self.metric_value)
        self.assertEqual(res, expected_result)

    def test_aggregate_and_report_exception_handling(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        mock_hub.aggregate_and_report.side_effect = Exception(f"agg_error_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=mock_hub)
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.aggregate_and_report(self.metric_name, self.metric_value)
        self.assertIn(f"agg_error_{self.rand_suffix}", str(ctx.exception))

    def test_generate_final_report_delegation(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        expected_report = {"report_id": self.rand_suffix}
        mock_hub.generate_final_report.return_value = expected_report

        bridge = AnomalyAuditBridge(audit_hub=mock_hub)
        res = bridge.generate_final_report()

        mock_hub.generate_final_report.assert_called_once()
        self.assertEqual(res, expected_report)

    def test_generate_final_report_exception_handling(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        mock_hub.generate_final_report.side_effect = Exception(f"gen_error_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=mock_hub)
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.generate_final_report()
        self.assertIn(f"gen_error_{self.rand_suffix}", str(ctx.exception))

    def test_export_json_report_delegation(self):
        mock_exporter = MagicMock()
        expected_path = f"/tmp/{uuid.uuid4().hex}.json"
        mock_exporter.export_json_report.return_value = expected_path

        bridge = AnomalyAuditBridge(audit_hub=MagicMock(), digest_exporter=mock_exporter)
        res = bridge.export_json_report(self.output_path)

        mock_exporter.export_json_report.assert_called_once_with(self.output_path)
        self.assertEqual(res, expected_path)

    def test_export_json_report_exception_handling(self):
        mock_exporter = MagicMock()
        mock_exporter.export_json_report.side_effect = Exception(f"json_err_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=MagicMock(), digest_exporter=mock_exporter)
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.export_json_report(self.output_path)
        self.assertIn(f"json_err_{self.rand_suffix}", str(ctx.exception))

    def test_export_html_report_delegation(self):
        mock_exporter = MagicMock()
        expected_path = f"/tmp/{uuid.uuid4().hex}.html"
        mock_exporter.export_html_report.return_value = expected_path

        bridge = AnomalyAuditBridge(audit_hub=MagicMock(), digest_exporter=mock_exporter)
        res = bridge.export_html_report(self.html_output_path)

        mock_exporter.export_html_report.assert_called_once_with(self.html_output_path)
        self.assertEqual(res, expected_path)

    def test_export_html_report_exception_handling(self):
        mock_exporter = MagicMock()
        mock_exporter.export_html_report.side_effect = Exception(f"html_err_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=MagicMock(), digest_exporter=mock_exporter)
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.export_html_report(self.html_output_path)
        self.assertIn(f"html_err_{self.rand_suffix}", str(ctx.exception))

    def test_export_stream_to_json_delegation(self):
        mock_exporter = MagicMock()
        expected_path = f"/tmp/stream_{uuid.uuid4().hex}.json"
        mock_exporter.export_stream_to_json.return_value = expected_path

        bridge = AnomalyAuditBridge(audit_hub=MagicMock(), digest_exporter=mock_exporter)
        res = bridge.export_stream_to_json(self.stream_id, self.output_path)

        mock_exporter.export_stream_to_json.assert_called_once_with(self.stream_id, self.output_path)
        self.assertEqual(res, expected_path)

    def test_export_stream_to_json_exception_handling(self):
        mock_exporter = MagicMock()
        mock_exporter.export_stream_to_json.side_effect = Exception(f"stream_err_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=MagicMock(), digest_exporter=mock_exporter)
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.export_stream_to_json(self.stream_id, self.output_path)
        self.assertIn(f"stream_err_{self.rand_suffix}", str(ctx.exception))

    def test_process_and_export_success(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        report_data = {"summary": uuid.uuid4().hex}
        mock_hub.generate_final_report.return_value = report_data

        mock_exporter = MagicMock()
        stability_digest_mock = MagicMock()
        mock_exporter.stability_digest = stability_digest_mock
        expected_file = f"/tmp/final_{uuid.uuid4().hex}.json"
        mock_exporter.export_json_report.return_value = expected_file

        bridge = AnomalyAuditBridge(audit_hub=mock_hub, digest_exporter=mock_exporter)
        res = bridge.process_and_export(self.output_path)

        mock_hub.generate_final_report.assert_called_once()
        stability_digest_mock.add_digest.assert_called_once_with(report_data)
        mock_exporter.export_json_report.assert_called_once_with(self.output_path)
        self.assertEqual(res, expected_file)

    def test_process_and_export_without_stability_digest(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        report_data = {"summary": uuid.uuid4().hex}
        mock_hub.generate_final_report.return_value = report_data

        mock_exporter = MagicMock(spec=[])
        expected_file = f"/tmp/final_{uuid.uuid4().hex}.json"
        mock_exporter.export_json_report = MagicMock(return_value=expected_file)

        bridge = AnomalyAuditBridge(audit_hub=mock_hub, digest_exporter=mock_exporter)
        res = bridge.process_and_export(self.output_path)

        mock_hub.generate_final_report.assert_called_once()
        mock_exporter.export_json_report.assert_called_once_with(self.output_path)
        self.assertEqual(res, expected_file)

    def test_process_and_export_exception_handling(self):
        mock_hub = MagicMock(spec=AnomalyAuditHub)
        mock_hub.generate_final_report.side_effect = Exception(f"process_err_{self.rand_suffix}")

        bridge = AnomalyAuditBridge(audit_hub=mock_hub, digest_exporter=MagicMock())
        with self.assertRaises(AnomalyAuditBridgeError) as ctx:
            bridge.process_and_export(self.output_path)
        self.assertIn(f"process_err_{self.rand_suffix}", str(ctx.exception))
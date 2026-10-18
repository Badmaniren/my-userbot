import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import json
import uuid
import random
import io

from skills.audit_export_engine import AuditExportEngine


class TestAuditExportEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/{uuid.uuid4().hex}"
        self.log_path_val = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold_val = random.uniform(0.1, 9.9)
        self.export_file_path = f"/tmp/{uuid.uuid4().hex}/report_{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.export_file_path):
            try:
                os.remove(self.export_file_path)
                os.rmdir(os.path.dirname(self.export_file_path))
            except OSError:
                pass

    def test_end_to_end_audit_export_composition(self):
        source_name = f"source_{uuid.uuid4().hex}"
        severity_val = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details_val = f"details_{uuid.uuid4().hex}"
        telemetry_val = {"cpu": random.randint(1, 100), "ram": uuid.uuid4().hex}

        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.random() * 100

        mock_hub = MagicMock()
        mock_logger = MagicMock()

        expected_final_report = {"status": "ok", "id": uuid.uuid4().hex}
        mock_hub.generate_final_report.return_value = expected_final_report

        mock_aggregator_response = {"metric": metric_name, "val": metric_value}
        mock_hub.aggregate_and_report.return_value = mock_aggregator_response

        mock_anomalies = [
            {"source": source_name, "severity": severity_val, "details": details_val},
            uuid.uuid4().hex
        ]
        mock_logger.get_anomalies.return_value = mock_anomalies
        mock_logger.get_structured_report.return_value = {"structured": True, "token": uuid.uuid4().hex}

        engine = AuditExportEngine(
            repo_path=self.repo_path_val,
            log_path=self.log_path_val,
            threshold=self.threshold_val,
            audit_hub=mock_hub,
            logger=mock_logger
        )

        res_log = engine.log_and_export_anomaly(
            source=source_name,
            severity=severity_val,
            details=details_val,
            telemetry_snapshot=telemetry_val
        )
        mock_hub.log_anomaly.assert_called_once_with(
            source=source_name,
            severity=severity_val,
            details=details_val,
            telemetry_snapshot=telemetry_val
        )
        mock_logger.log_anomaly.assert_called_once_with(
            source=source_name,
            severity=severity_val,
            details=details_val,
            telemetry_snapshot=telemetry_val
        )
        self.assertEqual(res_log, expected_final_report)

        res_agg = engine.aggregate_metric_and_export(metric_name=metric_name, value=metric_value)
        mock_hub.aggregate_and_report.assert_called_once_with(metric_name=metric_name, value=metric_value)
        self.assertEqual(res_agg, mock_aggregator_response)

        res_struct = engine.export_structured_logs()
        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(res_struct, mock_logger.get_structured_report.return_value)

        engine.clear_audit_history()
        mock_logger.clear_logs.assert_called_once()

        res_stream = engine.stream_export_data()
        mock_logger.get_anomalies.assert_called()
        self.assertEqual(res_stream, mock_anomalies)

        with patch("builtins.open", mock_open()) as mock_file_open:
            exported_path = engine.export_audit_report(self.export_file_path)
            self.assertEqual(exported_path, self.export_file_path)
            mock_logger.get_anomalies.assert_called()
            mock_hub.generate_final_report.assert_called()

    def test_default_initialization_instantiates_skills(self):
        with patch("skills.audit_export_engine.AnomalyAuditHub") as mock_hub_cls, \
             patch("skills.audit_export_engine.AnomalyLogger") as mock_logger_cls:

            instance = AuditExportEngine(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )

            mock_hub_cls.assert_called_once_with(
                repo_path=self.repo_path_val,
                log_path=self.log_path_val,
                threshold=self.threshold_val
            )
            mock_logger_cls.assert_called_once_with(
                log_path=self.log_path_val
            )
            self.assertEqual(instance.audit_hub, mock_hub_cls.return_value)
            self.assertEqual(instance.logger, mock_logger_cls.return_value)
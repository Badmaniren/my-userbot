import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.anomaly_pipeline import AnomalyPipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyPipeline(unittest.TestCase):

    def setUp(self):
        self.random_repo = f"/repo/{uuid.uuid4().hex}"
        self.random_log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.random_threshold = random.uniform(0.1, 9.9)

    @patch('skills.anomaly_pipeline.AnomalyAuditHub')
    @patch('skills.anomaly_pipeline.AnomalyLogger')
    def test_pipeline_initialization(self, mock_logger_cls, mock_audit_hub_cls):
        instance_id = uuid.uuid4().hex
        pipeline = AnomalyPipeline(
            repo_path=self.random_repo,
            log_path=self.random_log_path,
            threshold=self.random_threshold
        )
        mock_audit_hub_cls.assert_called_once_with(
            repo_path=self.random_repo,
            log_path=self.random_log_path,
            threshold=self.random_threshold
        )
        mock_logger_cls.assert_called_once_with(log_path=self.random_log_path)
        self.assertIsNotNone(pipeline)

    def test_process_and_log_anomaly_integration(self):
        source_val = ''.join(random.choices(string.ascii_letters, k=10))
        severity_val = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        details_val = {'detail_id': uuid.uuid4().hex, 'value': random.randint(1, 100)}
        telemetry_val = {'cpu_usage': random.uniform(10.0, 99.9)}

        with patch('skills.anomaly_pipeline.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_pipeline.AnomalyLogger') as mock_logger_cls:

            mock_audit_instance = mock_audit_cls.return_value
            mock_logger_instance = mock_logger_cls.return_value

            pipeline = AnomalyPipeline(
                repo_path=self.random_repo,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            pipeline.process_anomaly(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )

            mock_audit_instance.log_anomaly.assert_called_once_with(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )
            mock_logger_instance.log_anomaly.assert_called_once_with(
                source=source_val,
                severity=severity_val,
                details=details_val,
                telemetry_snapshot=telemetry_val
            )

    def test_aggregate_telemetry_pipeline(self):
        metric_name = uuid.uuid4().hex
        metric_value = random.uniform(1.0, 1000.0)
        expected_report_id = uuid.uuid4().hex

        with patch('skills.anomaly_pipeline.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_pipeline.AnomalyLogger') as mock_logger_cls:

            mock_audit_instance = mock_audit_cls.return_value
            mock_audit_instance.aggregate_and_report.return_value = {
                'report_id': expected_report_id,
                'metric': metric_name,
                'val': metric_value
            }

            pipeline = AnomalyPipeline(
                repo_path=self.random_repo,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            result = pipeline.aggregate_pipeline_metric(metric_name, metric_value)

            mock_audit_instance.aggregate_and_report.assert_called_once_with(metric_name, metric_value)
            self.assertEqual(result['report_id'], expected_report_id)
            self.assertEqual(result['metric'], metric_name)
            self.assertEqual(result['val'], metric_value)

    def test_generate_pipeline_final_report(self):
        mock_final_data = {
            'summary': uuid.uuid4().hex,
            'total_anomalies': random.randint(0, 50)
        }

        with patch('skills.anomaly_pipeline.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_pipeline.AnomalyLogger') as mock_logger_cls:

            mock_audit_instance = mock_audit_cls.return_value
            mock_audit_instance.generate_final_report.return_value = mock_final_data

            pipeline = AnomalyPipeline(
                repo_path=self.random_repo,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            report = pipeline.generate_final_report()

            mock_audit_instance.generate_final_report.assert_called_once()
            self.assertEqual(report, mock_final_data)

    def test_pipeline_stream_logs_handling(self):
        stream_data = io.BytesIO(uuid.uuid4().hex.encode('utf-8'))

        with patch('skills.anomaly_pipeline.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_pipeline.AnomalyLogger') as mock_logger_cls:

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_structured_report.return_value = stream_data.read().decode('utf-8')

            pipeline = AnomalyPipeline(
                repo_path=self.random_repo,
                log_path=self.random_log_path,
                threshold=self.random_threshold
            )

            report_output = pipeline.get_pipeline_structured_report()
            mock_logger_instance.get_structured_report.assert_called_once()
            self.assertIsInstance(report_output, str)
            self.assertTrue(len(report_output) > 0)

if __name__ == '__main__':
    unittest.main()
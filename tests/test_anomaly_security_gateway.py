import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

# Иммитируем модули, требуемые композицией, до импорта тестируемого модуля,
# чтобы предотвратить ImportError, если структура проекта еще не развернута.
if 'skills.anomaly_audit_hub' not in sys.modules:
    audit_hub_mod = ModuleType('skills.anomaly_audit_hub')
    class MockAnomalyAuditHub:
        def __init__(self, repo_path, log_path, threshold):
            self.repo_path = repo_path
            self.log_path = log_path
            self.threshold = threshold
        def log_anomaly(self, source, severity, details, telemetry_snapshot):
            return True
        def aggregate_and_report(self, metric_name, value):
            return True
        def generate_final_report(self):
            return {}
    audit_hub_mod.AnomalyAuditHub = MockAnomalyAuditHub
    sys.modules['skills.anomaly_audit_hub'] = audit_hub_mod

if 'skills.anomaly_filter' not in sys.modules:
    filter_mod = ModuleType('skills.anomaly_filter')
    def mock_start_new(data):
        return data
    class MockAnomalyFilter:
        def __init__(self):
            pass
        def filter(self, raw_anomaly_data):
            return raw_anomaly_data
    filter_mod.start_new = mock_start_new
    filter_mod.AnomalyFilter = MockAnomalyFilter
    sys.modules['skills.anomaly_filter'] = filter_mod

from skills.anomaly_security_gateway import AnomalySecurityGateway, AnomalySecurityGatewayError


class TestAnomalySecurityGateway(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/var/log/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)

    def test_gateway_initialization_composition(self):
        with patch('skills.anomaly_security_gateway.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_security_gateway.AnomalyFilter') as mock_filter_cls:

            mock_audit_instance = MagicMock()
            mock_audit_cls.return_value = mock_audit_instance

            mock_filter_instance = MagicMock()
            mock_filter_cls.return_value = mock_filter_instance

            gateway = AnomalySecurityGateway(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            mock_audit_cls.assert_called_once_with(self.rand_repo, self.rand_log, self.rand_threshold)
            mock_filter_cls.assert_called_once()
            self.assertEqual(gateway.audit_hub, mock_audit_instance)
            self.assertEqual(gateway.filter_engine, mock_filter_instance)

    def test_process_and_secure_anomaly_success(self):
        rand_source = f"src_{uuid.uuid4().hex[:8]}"
        rand_severity = random.randint(1, 10)
        rand_detail_key = f"key_{uuid.uuid4().hex[:6]}"
        rand_detail_val = f"val_{uuid.uuid4().hex[:6]}"
        rand_details = {rand_detail_key: rand_detail_val}

        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_metric_val = random.random()

        raw_input_data = {
            "source": rand_source,
            "severity": rand_severity,
            "details": rand_details,
            "metric": rand_metric,
            "metric_value": rand_metric_val
        }

        with patch('skills.anomaly_security_gateway.AnomalyAuditHub') as mock_audit_cls, \
             patch('skills.anomaly_security_gateway.AnomalyFilter') as mock_filter_cls:

            mock_audit_instance = MagicMock()
            mock_audit_cls.return_value = mock_audit_instance

            mock_filter_instance = MagicMock()
            filtered_result = {**raw_input_data, "filtered": True}
            mock_filter_instance.filter.return_value = filtered_result
            mock_filter_cls.return_value = mock_filter_instance

            gateway = AnomalySecurityGateway(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            result = gateway.process_and_secure_anomaly(raw_input_data)

            mock_filter_instance.filter.assert_called_once_with(raw_input_data)
            mock_audit_instance.log_anomaly.assert_called_once()

            args, _ = mock_audit_instance.log_anomaly.call_args
            self.assertEqual(args[0], rand_source)
            self.assertEqual(args[1], rand_severity)
            self.assertEqual(args[2], rand_details)

            mock_audit_instance.aggregate_and_report.assert_called_once_with(rand_metric, rand_metric_val)
            self.assertEqual(result, filtered_result)

    def test_process_and_secure_anomaly_with_start_new_integration(self):
        rand_data_chunk = f"data_{uuid.uuid4().hex}"

        with patch('skills.anomaly_security_gateway.AnomalyAuditHub'), \
             patch('skills.anomaly_security_gateway.AnomalyFilter'), \
             patch('skills.anomaly_security_gateway.start_new') as mock_start_new:

            mock_start_new.return_value = rand_data_chunk

            gateway = AnomalySecurityGateway(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            res = gateway.ingest_raw_stream(rand_data_chunk)
            mock_start_new.assert_called_once_with(rand_data_chunk)
            self.assertEqual(res, rand_data_chunk)

    def test_gateway_exception_handling(self):
        rand_error_msg = f"err_{uuid.uuid4().hex}"

        with patch('skills.anomaly_security_gateway.AnomalyAuditHub') as mock_audit_cls:
            mock_audit_instance = MagicMock()
            mock_audit_instance.log_anomaly.side_effect = Exception(rand_error_msg)
            mock_audit_cls.return_value = mock_audit_instance

            gateway = AnomalySecurityGateway(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            with self.assertRaises(AnomalySecurityGatewayError) as ctx:
                gateway.process_and_secure_anomaly({"source": "test", "severity": 1, "details": {}})

            self.assertIn(rand_error_msg, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.patch_quality_aggregator import PatchQualityAggregator, PatchQualityAggregatorError


class TestPatchQualityAggregator(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.log_path = f"/logs/{uuid.uuid4().hex}.log"
        self.policy = f"policy_{uuid.uuid4().hex}"

    def test_initialization_and_composition(self):
        with patch('skills.patch_quality_aggregator.PatchChecker') as mock_checker_cls, \
             patch('skills.patch_quality_aggregator.AnomalyLogger') as mock_logger_cls:

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)

            mock_checker_cls.assert_called_once_with(repo_path=self.repo_path, policy=self.policy)
            mock_logger_cls.assert_called_once_with(log_path=self.log_path)
            self.assertEqual(aggregator.repo_path, self.repo_path)
            self.assertEqual(aggregator.log_path, self.log_path)

    def test_aggregate_patch_quality_success(self):
        patch_content = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
        target_file = f"src/{uuid.uuid4().hex}.py"
        source_name = f"source_{uuid.uuid4().hex}"
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = f"details_{uuid.uuid4().hex}"
        telemetry = {"cpu": random.randint(1, 100), "memory": random.randint(100, 9999)}

        checker_result = {
            "status": "PASSED",
            "score": round(random.uniform(0.5, 1.0), 2),
            "issues_found": random.randint(0, 3)
        }

        anomaly_report = {
            "total_anomalies": 1,
            "anomalies": [{"source": source_name, "severity": severity, "details": details}]
        }

        with patch('skills.patch_quality_aggregator.PatchChecker') as mock_checker_cls, \
             patch('skills.patch_quality_aggregator.AnomalyLogger') as mock_logger_cls:

            mock_checker_instance = mock_checker_cls.return_value
            mock_checker_instance.check_patch.return_value = checker_result

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_structured_report.return_value = anomaly_report

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)

            # Логируем аномалию перед агрегацией, чтобы проверить интеграцию
            aggregator.log_anomaly_event(source=source_name, severity=severity, details=details, telemetry_snapshot=telemetry)

            result = aggregator.aggregate_and_evaluate(patch_content=patch_content, target_file=target_file)

            mock_checker_instance.check_patch.assert_called_once_with(patch_content=patch_content, target_file=target_file)
            mock_logger_instance.log_anomaly.assert_called_once_with(
                source=source_name,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )

            self.assertIn("patch_check", result)
            self.assertIn("anomaly_report", result)
            self.assertIn("security_state", result)
            self.assertEqual(result["patch_check"], checker_result)
            self.assertEqual(result["anomaly_report"], anomaly_report)
            self.assertEqual(result["security_state"], "CONSOLIDATED")

    def test_aggregate_patch_quality_checker_exception(self):
        patch_content = ''.join(random.choices(string.ascii_letters, k=32))
        target_file = f"core/{uuid.uuid4().hex}.cpp"
        error_msg = f"error_{uuid.uuid4().hex}"

        with patch('skills.patch_quality_aggregator.PatchChecker') as mock_checker_cls, \
             patch('skills.patch_quality_aggregator.AnomalyLogger'):

            mock_checker_instance = mock_checker_cls.return_value
            mock_checker_instance.check_patch.side_effect = Exception(error_msg)

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)

            with self.assertRaises(PatchQualityAggregatorError) as ctx:
                aggregator.aggregate_and_evaluate(patch_content=patch_content, target_file=target_file)

            self.assertIn(error_msg, str(ctx.exception))

    def test_stream_aggregation(self):
        stream_data = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)
        target_file = f"module_{uuid.uuid4().hex}.py"

        checker_result = {
            "status": "FAILED",
            "score": 0.1,
            "violations": [uuid.uuid4().hex]
        }

        with patch('skills.patch_quality_aggregator.PatchChecker') as mock_checker_cls, \
             patch('skills.patch_quality_aggregator.AnomalyLogger') as mock_logger_cls:

            mock_checker_instance = mock_checker_cls.return_value
            mock_checker_instance.check_stream.return_value = checker_result

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_structured_report.return_value = {"total_anomalies": 0}

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)
            result = aggregator.aggregate_stream(stream=stream_data, target_file=target_file)

            mock_checker_instance.check_stream.assert_called_once_with(stream=stream_data, target_file=target_file)
            self.assertEqual(result["patch_check"], checker_result)
            self.assertEqual(result["security_state"], "VULNERABLE")

    def test_clear_and_reset_logs(self):
        with patch('skills.patch_quality_aggregator.PatchChecker'), \
             patch('skills.patch_quality_aggregator.AnomalyLogger') as mock_logger_cls:

            mock_logger_instance = mock_logger_cls.return_value

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)
            aggregator.reset_security_logs()

            mock_logger_instance.clear_logs.assert_called_once()

    def test_get_anomalies_retrieval(self):
        expected_anomalies = [
            {"id": uuid.uuid4().hex, "severity": "HIGH"},
            {"id": uuid.uuid4().hex, "severity": "LOW"}
        ]

        with patch('skills.patch_quality_aggregator.PatchChecker'), \
             patch('skills.patch_quality_aggregator.AnomalyLogger') as mock_logger_cls:

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_anomalies.return_value = expected_anomalies

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)
            anomalies = aggregator.fetch_anomalies()

            mock_logger_instance.get_anomalies.assert_called_once()
            self.assertEqual(anomalies, expected_anomalies)

    def test_get_structured_report(self):
        raw_anomalies = [{"id": uuid.uuid4().hex, "severity": "HIGH"}]
        with patch('skills.patch_quality_aggregator.PatchChecker'), \
             patch('skills.patch_quality_aggregator.AnomalyLogger') as mock_logger_cls:

            mock_logger_instance = mock_logger_cls.return_value
            mock_logger_instance.get_structured_report.return_value = raw_anomalies
            mock_logger_instance.get_anomalies.return_value = raw_anomalies

            aggregator = PatchQualityAggregator(repo_path=self.repo_path, log_path=self.log_path, policy=self.policy)
            report = aggregator.get_structured_report()

            self.assertIsInstance(report, dict)
            self.assertEqual(report["total_anomalies"], 1)
            self.assertEqual(report["anomalies"], raw_anomalies)


if __name__ == '__main__':
    unittest.main()
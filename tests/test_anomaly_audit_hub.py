import io
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import uuid

from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_report_aggregator import AnomalyReportAggregatorError


def _rand_str(prefix=""):
    return f"{prefix}{uuid.uuid4().hex}"


def _rand_dict():
    return {_rand_str("k_"): _rand_str("v_") for _ in range(random.randint(1, 5))}


def _rand_float():
    return round(random.uniform(0.001, 9999.99), 4)


class TestAnomalyAuditHub(unittest.TestCase):

    def test_init_wires_logger_and_aggregator_correctly(self):
        repo_path = f"/tmp/repo_{_rand_str()}"
        log_path = f"/tmp/log_{_rand_str()}.log"
        threshold = _rand_float()

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_agg_cls:

            mock_logger_inst = MagicMock()
            mock_agg_inst = MagicMock()
            mock_logger_cls.return_value = mock_logger_inst
            mock_agg_cls.return_value = mock_agg_inst

            hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

            mock_logger_cls.assert_called_once_with(log_path=log_path)
            mock_agg_cls.assert_called_once_with(
                repo_path=repo_path,
                log_path=log_path,
                threshold=threshold,
                logger=mock_logger_inst
            )
            self.assertIs(hub.logger, mock_logger_inst)
            self.assertIs(hub.aggregator, mock_agg_inst)

    def test_log_anomaly_passes_arguments_and_returns_logger_output(self):
        repo_path = f"/var/repo_{_rand_str()}"
        log_path = f"/var/log_{_rand_str()}.log"
        threshold = _rand_float()

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator"):

            mock_logger_inst = MagicMock()
            expected_log_result = {
                _rand_str("log_key_"): _rand_str("log_val_"),
                "token": _rand_str("tok_")
            }
            mock_logger_inst.log_anomaly.return_value = expected_log_result
            mock_logger_cls.return_value = mock_logger_inst

            hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

            source = _rand_str("src_")
            severity = _rand_str("sev_")
            details = _rand_dict()
            telemetry = _rand_dict()

            result = hub.log_anomaly(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )

            mock_logger_inst.log_anomaly.assert_called_once_with(
                source=source,
                severity=severity,
                details=details,
                telemetry_snapshot=telemetry
            )
            self.assertEqual(result, expected_log_result)

    def test_log_anomaly_defaults_none_for_optional_parameters(self):
        repo_path = f"/path/{_rand_str()}"
        log_path = f"/path/{_rand_str()}.log"
        threshold = _rand_float()

        with patch("skills.anomaly_audit_hub.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator"):

            mock_logger_inst = MagicMock()
            mock_logger_cls.return_value = mock_logger_inst

            hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

            source = _rand_str("src_")
            severity = _rand_str("sev_")

            hub.log_anomaly(source=source, severity=severity)

            mock_logger_inst.log_anomaly.assert_called_once_with(
                source=source,
                severity=severity,
                details=None,
                telemetry_snapshot=None
            )

    def test_aggregate_and_report_delegates_to_aggregator(self):
        repo_path = f"/home/user/repo_{_rand_str()}"
        log_path = f"/home/user/log_{_rand_str()}.txt"
        threshold = _rand_float()

        with patch("skills.anomaly_audit_hub.AnomalyLogger"), \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_agg_cls:

            mock_agg_inst = MagicMock()
            expected_agg_result = {
                "status": _rand_str("status_"),
                "metric_value": _rand_float(),
                "trace_id": _rand_str("tr_")
            }
            mock_agg_inst.aggregate_and_report.return_value = expected_agg_result
            mock_agg_cls.return_value = mock_agg_inst

            hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

            metric_name = _rand_str("metric_")
            metric_val = _rand_float()

            result = hub.aggregate_and_report(metric_name=metric_name, value=metric_val)

            mock_agg_inst.aggregate_and_report.assert_called_once_with(
                metric_name=metric_name,
                value=metric_val
            )
            self.assertEqual(result, expected_agg_result)

    def test_generate_final_report_delegates_to_aggregator(self):
        repo_path = f"/opt/repo_{_rand_str()}"
        log_path = f"/opt/log_{_rand_str()}.json"
        threshold = _rand_float()

        with patch("skills.anomaly_audit_hub.AnomalyLogger"), \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_agg_cls:

            mock_agg_inst = MagicMock()
            expected_report = {
                "report_id": _rand_str("rep_"),
                "summary": _rand_dict(),
                "total_events": random.randint(10, 500)
            }
            mock_agg_inst.generate_final_report.return_value = expected_report
            mock_agg_cls.return_value = mock_agg_inst

            hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

            report = hub.generate_final_report()

            mock_agg_inst.generate_final_report.assert_called_once_with()
            self.assertEqual(report, expected_report)

    def test_aggregate_and_report_propagates_exceptions(self):
        repo_path = f"/mnt/{_rand_str()}"
        log_path = f"/mnt/{_rand_str()}.log"
        threshold = _rand_float()

        with patch("skills.anomaly_audit_hub.AnomalyLogger"), \
             patch("skills.anomaly_audit_hub.AnomalyReportAggregator") as mock_agg_cls:

            mock_agg_inst = MagicMock()
            error_message = _rand_str("agg_err_")
            mock_agg_inst.aggregate_and_report.side_effect = AnomalyReportAggregatorError(error_message)
            mock_agg_cls.return_value = mock_agg_inst

            hub = AnomalyAuditHub(repo_path=repo_path, log_path=log_path, threshold=threshold)

            metric_name = _rand_str("metric_fail_")
            val = _rand_float()

            with self.assertRaises(AnomalyReportAggregatorError) as ctx:
                hub.aggregate_and_report(metric_name=metric_name, value=val)

            self.assertIn(error_message, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
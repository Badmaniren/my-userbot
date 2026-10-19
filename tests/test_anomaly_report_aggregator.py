import io
import random
import string
import unittest
from unittest.mock import MagicMock, patch
import uuid

from skills.anomaly_correlator import AnomalyCorrelatorError
from skills.anomaly_report_aggregator import (
    AnomalyReportAggregator,
    AnomalyReportAggregatorError,
)


class TestAnomalyReportAggregator(unittest.TestCase):
    def _random_str(self, length=8):
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=length))

    def _random_path(self):
        return f"/tmp/{uuid.uuid4().hex}/{self._random_str(6)}.log"

    def test_init_with_custom_logger_and_correlator(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )
        self.assertIs(aggregator.anomaly_logger, mock_logger)
        self.assertIs(aggregator.correlator, mock_correlator)

    def test_init_creates_defaults_when_omitted(self):
        random_repo = f"/repo/{uuid.uuid4().hex}"
        random_log = self._random_path()
        random_thresh = random.uniform(1.0, 50.0)

        with patch("skills.anomaly_report_aggregator.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_report_aggregator.AnomalyCorrelator") as mock_correlator_cls:
            instance_logger = MagicMock()
            mock_logger_cls.return_value = instance_logger
            instance_correlator = MagicMock()
            mock_correlator_cls.return_value = instance_correlator

            aggregator = AnomalyReportAggregator(
                repo_path=random_repo,
                log_path=random_log,
                threshold=random_thresh,
            )

            mock_logger_cls.assert_called_once_with(log_path=random_log)
            mock_correlator_cls.assert_called_once_with(
                repo_path=random_repo,
                log_path=random_log,
                threshold=random_thresh,
                detector=None,
                logger=instance_logger,
            )
            self.assertIs(aggregator.anomaly_logger, instance_logger)
            self.assertIs(aggregator.correlator, instance_correlator)

    def test_aggregate_and_report_success_with_dicts_and_non_dicts(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_val = random.uniform(10.0, 100.0)

        expected_source = f"src_{uuid.uuid4().hex}"
        expected_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        expected_details = f"details_{uuid.uuid4().hex}"
        expected_telemetry = {f"k_{self._random_str(4)}": random.randint(1, 100)}

        raw_str_anomaly = f"string_err_{uuid.uuid4().hex}"

        mock_correlator.correlate_events.return_value = [
            {
                "source": expected_source,
                "severity": expected_severity,
                "details": expected_details,
                "telemetry_snapshot": expected_telemetry,
            },
            raw_str_anomaly,
        ]

        expected_report = {
            "token": uuid.uuid4().hex,
            "count": 2,
            "status": "COMPLETED",
        }
        mock_logger.get_structured_report.return_value = expected_report

        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )
        report = aggregator.aggregate_and_report(metric_name, metric_val)

        mock_correlator.correlate_metric.assert_called_once_with(metric_name, metric_val)
        mock_correlator.correlate_events.assert_called_once()

        self.assertEqual(mock_logger.log_anomaly.call_count, 2)
        mock_logger.log_anomaly.assert_any_call(
            source=expected_source,
            severity=expected_severity,
            details=expected_details,
            telemetry_snapshot=expected_telemetry,
        )
        mock_logger.log_anomaly.assert_any_call(
            source=raw_str_anomaly,
            severity="UNKNOWN",
            details=raw_str_anomaly,
            telemetry_snapshot={},
        )
        self.assertEqual(report, expected_report)

    def test_aggregate_and_report_correlator_error_wrapped(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        err_msg = f"correlator_failure_{uuid.uuid4().hex}"
        mock_correlator.correlate_events.side_effect = AnomalyCorrelatorError(err_msg)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )
        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_and_report(uuid.uuid4().hex, random.random())

        self.assertIn(err_msg, str(ctx.exception))

    def test_aggregate_execution_flow_casts_numeric_strings_and_handles_mixed(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        numeric_float_val = round(random.uniform(1.5, 99.5), 3)
        numeric_str_val = str(numeric_float_val)
        non_numeric_str = f"non_num_{uuid.uuid4().hex}"
        already_int = random.randint(100, 200)

        payload_input = {
            "castable": numeric_str_val,
            "non_castable": non_numeric_str,
            "int_val": already_int,
        }

        execution_id = f"exec_{uuid.uuid4().hex}"
        expected_anomaly_source = f"src_{uuid.uuid4().hex}"
        mock_correlator.analyze_execution_flow.return_value = [
            {
                "source": expected_anomaly_source,
                "severity": "CRITICAL",
                "details": "High deviation detected",
                "telemetry_snapshot": {"val": numeric_float_val},
            }
        ]
        mock_report = {"flow_report_id": uuid.uuid4().hex, "anomalies_count": 1}
        mock_logger.get_structured_report.return_value = mock_report

        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )
        result = aggregator.aggregate_execution_flow(execution_id, payload_input)

        mock_correlator.analyze_execution_flow.assert_called_once()
        called_exec_id, called_payload = mock_correlator.analyze_execution_flow.call_args[0]
        self.assertEqual(called_exec_id, execution_id)
        self.assertIsInstance(called_payload["castable"], float)
        self.assertAlmostEqual(called_payload["castable"], numeric_float_val)
        self.assertNotIn("non_castable", called_payload)
        self.assertEqual(called_payload["int_val"], float(already_int))

        mock_logger.log_anomaly.assert_called_once_with(
            source=expected_anomaly_source,
            severity="CRITICAL",
            details="High deviation detected",
            telemetry_snapshot={"val": numeric_float_val},
        )
        self.assertEqual(result, mock_report)

    def test_aggregate_execution_flow_correlator_exception_wrapped(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        type_err_msg = f"'>' not supported between instances of 'str' and 'float' - {uuid.uuid4().hex}"
        mock_correlator.analyze_execution_flow.side_effect = TypeError(type_err_msg)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_execution_flow(uuid.uuid4().hex, {"metric": "invalid"})

        self.assertIn(type_err_msg, str(ctx.exception))

    def test_generate_final_report_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        random_report = {
            "summary_id": uuid.uuid4().hex,
            "metrics": {self._random_str(5): random.random()},
        }
        mock_logger.get_structured_report.return_value = random_report

        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )
        report = aggregator.generate_final_report()

        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(report, random_report)

    def test_generate_final_report_exception_wrapped(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        err_text = f"logger_failure_{uuid.uuid4().hex}"
        mock_logger.get_structured_report.side_effect = RuntimeError(err_text)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger, correlator=mock_correlator
        )
        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.generate_final_report()

        self.assertIn(err_text, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
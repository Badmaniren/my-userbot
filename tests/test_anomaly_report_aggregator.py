import random
import unittest
from unittest.mock import MagicMock, patch
import uuid

from skills.anomaly_correlator import AnomalyCorrelatorError
from skills.anomaly_report_aggregator import (
    AnomalyReportAggregator,
    AnomalyReportAggregatorError,
)


class TestAnomalyReportAggregatorInquisition(unittest.TestCase):
    def _random_str(self, length=8):
        return f"str_{uuid.uuid4().hex[:length]}"

    def _random_float(self, start=0.1, end=100.0):
        return round(random.uniform(start, end), 4)

    def test_init_with_custom_logger_and_correlator(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        repo = f"/path/{self._random_str()}"
        log_p = f"/logs/{self._random_str()}.log"
        thresh = self._random_float(1.0, 10.0)

        aggregator = AnomalyReportAggregator(
            repo_path=repo,
            log_path=log_p,
            threshold=thresh,
            correlator=mock_correlator,
            logger=mock_logger,
        )

        self.assertIs(aggregator.anomaly_logger, mock_logger)
        self.assertIs(aggregator.correlator, mock_correlator)

    def test_init_creates_defaults_when_none(self):
        repo = f"/repo/{self._random_str()}"
        log_p = f"/var/log/{self._random_str()}.log"
        thresh = self._random_float()
        detector = MagicMock()

        with patch("skills.anomaly_report_aggregator.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_report_aggregator.AnomalyCorrelator") as mock_correlator_cls:
            fake_logger_inst = MagicMock()
            fake_correlator_inst = MagicMock()
            mock_logger_cls.return_value = fake_logger_inst
            mock_correlator_cls.return_value = fake_correlator_inst

            aggregator = AnomalyReportAggregator(
                repo_path=repo,
                log_path=log_p,
                threshold=thresh,
                detector=detector,
            )

            mock_logger_cls.assert_called_once_with(log_path=log_p)
            mock_correlator_cls.assert_called_once_with(
                repo_path=repo,
                log_path=log_p,
                threshold=thresh,
                detector=detector,
                logger=fake_logger_inst,
            )
            self.assertIs(aggregator.anomaly_logger, fake_logger_inst)
            self.assertIs(aggregator.correlator, fake_correlator_inst)

    def test_log_anomaly_dict_format(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        src = self._random_str()
        sev = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        details = {self._random_str(): self._random_str()}
        telemetry = {self._random_str(): self._random_float()}

        anomaly_dict = {
            "source": src,
            "severity": sev,
            "details": details,
            "telemetry_snapshot": telemetry,
        }

        aggregator._log_anomaly(anomaly_dict)
        mock_logger.log_anomaly.assert_called_once_with(
            source=src,
            severity=sev,
            details=details,
            telemetry_snapshot=telemetry,
        )

    def test_log_anomaly_str_format(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        raw_str = f"anomaly_msg_{self._random_str()}"
        aggregator._log_anomaly(raw_str)

        mock_logger.log_anomaly.assert_called_once_with(
            source=raw_str,
            severity="MEDIUM",
            details={"message": raw_str},
            telemetry_snapshot=None,
        )

    def test_log_anomaly_object_format(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        class CustomAnomaly:
            pass

        obj = CustomAnomaly()
        obj.source = self._random_str()
        obj.severity = random.choice(["INFO", "WARNING", "FATAL"])
        obj.details = {self._random_str(): random.randint(1, 100)}
        obj.telemetry_snapshot = {self._random_str(): self._random_float()}

        aggregator._log_anomaly(obj)

        mock_logger.log_anomaly.assert_called_once_with(
            source=obj.source,
            severity=obj.severity,
            details=obj.details,
            telemetry_snapshot=obj.telemetry_snapshot,
        )

    def test_aggregate_and_report_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        metric = f"metric_{self._random_str()}"
        val = self._random_float()
        expected_report = {
            "token": uuid.uuid4().hex,
            "status": "OK",
            "count": random.randint(1, 10),
        }

        anomaly_sample = {
            "source": self._random_str(),
            "severity": "HIGH",
            "details": {self._random_str(): self._random_str()},
            "telemetry_snapshot": None,
        }

        mock_correlator.correlate_events.return_value = [anomaly_sample]
        mock_logger.get_structured_report.return_value = expected_report

        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)
        res = aggregator.aggregate_and_report(metric, val)

        mock_correlator.correlate_metric.assert_called_once_with(metric, val)
        mock_correlator.correlate_events.assert_called_once()
        mock_logger.log_anomaly.assert_called_once_with(
            source=anomaly_sample["source"],
            severity=anomaly_sample["severity"],
            details=anomaly_sample["details"],
            telemetry_snapshot=anomaly_sample["telemetry_snapshot"],
        )
        self.assertEqual(res, expected_report)

    def test_aggregate_and_report_raises_custom_error(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        err_msg = f"correlator_err_{self._random_str()}"
        mock_correlator.correlate_metric.side_effect = AnomalyCorrelatorError(err_msg)

        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_and_report(self._random_str(), self._random_float())

        self.assertIn(err_msg, str(ctx.exception))

    def test_aggregate_execution_flow_sanitizes_str_numbers(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        exec_id = f"exec_{uuid.uuid4().hex}"
        float_num = self._random_float(10.0, 50.0)
        non_numeric_str = f"status_text_{self._random_str()}"

        payload = {
            "val_str_numeric": str(float_num),
            "val_pure_str": non_numeric_str,
            "val_already_float": 12.34,
        }

        expected_report = {"report_id": uuid.uuid4().hex}
        mock_correlator.analyze_execution_flow.return_value = []
        mock_logger.get_structured_report.return_value = expected_report

        result = aggregator.aggregate_execution_flow(exec_id, payload)

        mock_correlator.analyze_execution_flow.assert_called_once()
        called_args = mock_correlator.analyze_execution_flow.call_args[0]
        self.assertEqual(called_args[0], exec_id)
        sanitized_payload = called_args[1]

        self.assertEqual(sanitized_payload["val_str_numeric"], float_num)
        self.assertEqual(sanitized_payload["val_pure_str"], non_numeric_str)
        self.assertEqual(sanitized_payload["val_already_float"], 12.34)
        self.assertEqual(result, expected_report)

    def test_aggregate_execution_flow_logs_anomalies(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        exec_id = f"exec_{uuid.uuid4().hex}"
        anomaly_one = {"source": self._random_str(), "severity": "LOW", "details": {}, "telemetry_snapshot": None}
        anomaly_two = self._random_str()

        mock_correlator.analyze_execution_flow.return_value = [anomaly_one, anomaly_two]
        expected_report = {"generated_id": uuid.uuid4().hex}
        mock_logger.get_structured_report.return_value = expected_report

        res = aggregator.aggregate_execution_flow(exec_id, {})

        self.assertEqual(mock_logger.log_anomaly.call_count, 2)
        self.assertEqual(res, expected_report)

    def test_aggregate_execution_flow_exception_handling(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        err_text = f"critical_failure_{self._random_str()}"
        mock_correlator.analyze_execution_flow.side_effect = RuntimeError(err_text)

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_execution_flow(self._random_str(), {})

        self.assertIn(err_text, str(ctx.exception))

    def test_generate_final_report_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        expected_report = {
            "summary_hash": uuid.uuid4().hex,
            "metrics": {self._random_str(): random.randint(1, 100)},
        }
        mock_logger.get_structured_report.return_value = expected_report

        report = aggregator.generate_final_report()

        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(report, expected_report)

    def test_generate_final_report_raises_aggregator_error(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        internal_error = f"logger_err_{self._random_str()}"
        mock_logger.get_structured_report.side_effect = ValueError(internal_error)

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.generate_final_report()

        self.assertIn(internal_error, str(ctx.exception))

    def test_aggregate_execution_flow_with_non_numeric_metadata(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=mock_logger)

        exec_id = f"exec_{uuid.uuid4().hex}"
        payload = {
            "cpu_usage": 95.5,
            "memory_usage": "1024",
            "trace_id": str(uuid.uuid4()),
            "status_text": "processing"
        }

        mock_correlator.analyze_execution_flow.return_value = []
        expected_report = {"status": "ok"}
        mock_logger.get_structured_report.return_value = expected_report

        result = aggregator.aggregate_execution_flow(exec_id, payload)

        mock_correlator.analyze_execution_flow.assert_called_once()
        called_payload = mock_correlator.analyze_execution_flow.call_args[0][1]
        self.assertEqual(called_payload["memory_usage"], 1024.0)
        self.assertIsInstance(called_payload["memory_usage"], float)
        self.assertEqual(called_payload["trace_id"], payload["trace_id"])
        self.assertEqual(called_payload["status_text"], "processing")
        self.assertEqual(result, expected_report)


if __name__ == "__main__":
    unittest.main()
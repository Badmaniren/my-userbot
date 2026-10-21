import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.anomaly_report_aggregator import (
    AnomalyReportAggregator,
    AnomalyReportAggregatorError
)
from skills.anomaly_correlator import AnomalyCorrelatorError


class TestAnomalyReportAggregator(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_threshold = round(random.uniform(1.0, 100.0), 2)

    def test_init_default_dependencies(self):
        with patch("skills.anomaly_report_aggregator.AnomalyLogger") as mock_logger_cls, \
             patch("skills.anomaly_report_aggregator.AnomalyCorrelator") as mock_corr_cls:

            aggregator = AnomalyReportAggregator(
                repo_path=self.rand_repo,
                log_path=self.rand_log,
                threshold=self.rand_threshold
            )

            mock_logger_cls.assert_called_once_with(log_path=self.rand_log)
            mock_corr_cls.assert_called_once()

    def test_init_injected_dependencies(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        self.assertEqual(aggregator.anomaly_logger, mock_logger)
        self.assertEqual(aggregator.correlator, mock_correlator)

    def test_aggregate_and_report_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_metric = "".join(random.choices(string.ascii_lowercase, k=10))
        rand_value = random.randint(10, 1000)

        rand_source = "".join(random.choices(string.ascii_uppercase, k=5))
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = uuid.uuid4().hex
        rand_snapshot = {"cpu": random.randint(1, 100)}

        mock_correlator.correlate_events.return_value = [
            {
                "source": rand_source,
                "severity": rand_severity,
                "details": rand_details,
                "telemetry_snapshot": rand_snapshot
            }
        ]

        rand_report = {"status": uuid.uuid4().hex, "total": 1}
        mock_logger.get_structured_report.return_value = rand_report

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        result = aggregator.aggregate_and_report(rand_metric, rand_value)

        mock_correlator.correlate_metric.assert_called_once_with(rand_metric, rand_value)
        mock_correlator.correlate_events.assert_called_once()
        mock_logger.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )
        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(result, rand_report)

    def test_aggregate_and_report_raises_custom_error(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_metric = uuid.uuid4().hex
        rand_value = random.random()
        rand_error_msg = uuid.uuid4().hex

        mock_correlator.correlate_metric.side_effect = AnomalyCorrelatorError(rand_error_msg)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_and_report(rand_metric, rand_value)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_aggregate_execution_flow_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_exec_id = uuid.uuid4().hex
        rand_payload = {"data": uuid.uuid4().hex}

        rand_source = uuid.uuid4().hex
        rand_severity = uuid.uuid4().hex
        rand_details = uuid.uuid4().hex
        rand_snapshot = {"memory": random.randint(500, 2000)}

        mock_correlator.analyze_execution_flow.return_value = [
            {
                "source": rand_source,
                "severity": rand_severity,
                "details": rand_details,
                "telemetry_snapshot": rand_snapshot
            }
        ]

        rand_report = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_logger.get_structured_report.return_value = rand_report

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        result = aggregator.aggregate_execution_flow(rand_exec_id, rand_payload)

        mock_correlator.analyze_execution_flow.assert_called_once_with(rand_exec_id, rand_payload)
        mock_logger.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )
        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(result, rand_report)

    def test_aggregate_execution_flow_raises_custom_error(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_exec_id = uuid.uuid4().hex
        rand_payload = [random.randint(1, 10)]
        rand_error_msg = uuid.uuid4().hex

        mock_correlator.analyze_execution_flow.side_effect = RuntimeError(rand_error_msg)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_execution_flow(rand_exec_id, rand_payload)

        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_aggregate_execution_flow_reraises_aggregator_error(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_exec_id = uuid.uuid4().hex
        rand_payload = {}
        rand_error_msg = uuid.uuid4().hex

        mock_correlator.analyze_execution_flow.side_effect = AnomalyReportAggregatorError(rand_error_msg)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.aggregate_execution_flow(rand_exec_id, rand_payload)

        self.assertEqual(str(ctx.exception), rand_error_msg)

    def test_generate_final_report_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_report = {uuid.uuid4().hex: random.randint(1, 50)}
        mock_logger.get_structured_report.return_value = rand_report

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        result = aggregator.generate_final_report()

        mock_logger.get_structured_report.assert_called_once()
        self.assertEqual(result, rand_report)

    def test_generate_final_report_raises_error(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        rand_error_msg = uuid.uuid4().hex
        mock_logger.get_structured_report.side_effect = Exception(rand_error_msg)

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )

        with self.assertRaises(AnomalyReportAggregatorError) as ctx:
            aggregator.generate_final_report()

        self.assertIn(rand_error_msg, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
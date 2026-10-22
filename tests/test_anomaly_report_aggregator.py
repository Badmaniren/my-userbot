import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError


class TestAnomalyReportAggregator(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo/{uuid.uuid4().hex}"
        self.rand_log = f"/logs/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 9.9)
        self.rand_detector = f"detector_{uuid.uuid4().hex[:6]}"
        
        self.aggregator = AnomalyReportAggregator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            detector=self.rand_detector
        )

    @patch('skills.anomaly_report_aggregator.AnomalyCorrelator')
    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    def test_initialization_and_composition(self, mock_logger_cls, mock_correlator_cls):
        rand_repo_local = f"/repo/{uuid.uuid4().hex}"
        rand_log_local = f"/logs/{uuid.uuid4().hex}.log"
        rand_threshold_local = random.uniform(1.0, 5.0)
        rand_detector_local = f"det_{uuid.uuid4().hex}"

        instance = AnomalyReportAggregator(
            repo_path=rand_repo_local,
            log_path=rand_log_local,
            threshold=rand_threshold_local,
            detector=rand_detector_local
        )

        mock_correlator_cls.assert_called_once_with(
            repo_path=rand_repo_local,
            log_path=rand_log_local,
            threshold=rand_threshold_local,
            detector=rand_detector_local,
            logger=instance.anomaly_logger
        )
        mock_logger_cls.assert_called_once_with(log_path=rand_log_local)

    @patch('skills.anomaly_report_aggregator.AnomalyCorrelator')
    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    def test_aggregate_and_report_success(self, mock_logger_cls, mock_correlator_cls):
        mock_correlator_instance = mock_correlator_cls.return_value
        mock_logger_instance = mock_logger_cls.return_value

        rand_metric = f"metric_{uuid.uuid4().hex[:6]}"
        rand_value = random.randint(100, 999)
        rand_source = f"src_{uuid.uuid4().hex[:4]}"
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = f"details_{uuid.uuid4().hex}"
        rand_snapshot = {"telemetry_id": uuid.uuid4().hex}

        mock_correlator_instance.correlate_events.return_value = [
            {
                "source": rand_source,
                "severity": rand_severity,
                "details": rand_details,
                "telemetry_snapshot": rand_snapshot
            }
        ]

        rand_report = f"report_{uuid.uuid4().hex}"
        mock_logger_instance.get_structured_report.return_value = rand_report

        aggregator = AnomalyReportAggregator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            detector=self.rand_detector
        )

        result = aggregator.aggregate_and_report(rand_metric, rand_value)

        mock_correlator_instance.correlate_metric.assert_called_once_with(rand_metric, rand_value)
        mock_correlator_instance.correlate_events.assert_called_once()
        
        mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )
        mock_logger_instance.get_structured_report.assert_called_once()
        self.assertEqual(result, rand_report)

    @patch('skills.anomaly_report_aggregator.AnomalyCorrelator')
    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    def test_aggregate_execution_flow_success(self, mock_logger_cls, mock_correlator_cls):
        mock_correlator_instance = mock_correlator_cls.return_value
        mock_logger_instance = mock_logger_cls.return_value

        rand_exec_id = uuid.uuid4().hex
        rand_payload = {uuid.uuid4().hex: random.random()}
        
        rand_source = f"src_{uuid.uuid4().hex}"
        rand_severity = random.choice(["INFO", "WARNING", "FATAL"])
        rand_details = uuid.uuid4().hex
        rand_snapshot = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_correlator_instance.analyze_execution_flow.return_value = [
            {
                "source": rand_source,
                "severity": rand_severity,
                "details": rand_details,
                "telemetry_snapshot": rand_snapshot
            }
        ]
        
        rand_final_report = uuid.uuid4().hex
        mock_logger_instance.get_structured_report.return_value = rand_final_report

        aggregator = AnomalyReportAggregator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            detector=self.rand_detector
        )

        report = aggregator.aggregate_execution_flow(rand_exec_id, rand_payload)

        mock_correlator_instance.analyze_execution_flow.assert_called_once_with(rand_exec_id, rand_payload)
        mock_logger_instance.log_anomaly.assert_called_once_with(
            source=rand_source,
            severity=rand_severity,
            details=rand_details,
            telemetry_snapshot=rand_snapshot
        )
        self.assertEqual(report, rand_final_report)

    @patch('skills.anomaly_report_aggregator.AnomalyCorrelator')
    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    def test_correlator_error_handling(self, mock_logger_cls, mock_correlator_cls):
        from skills.anomaly_correlator import AnomalyCorrelatorError
        mock_correlator_instance = mock_correlator_cls.return_value
        mock_correlator_instance.correlate_metric.side_effect = AnomalyCorrelatorError(uuid.uuid4().hex)

        aggregator = AnomalyReportAggregator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            detector=self.rand_detector
        )

        with self.assertRaises(AnomalyReportAggregatorError):
            aggregator.aggregate_and_report(uuid.uuid4().hex, random.randint(1, 100))

    @patch('skills.anomaly_report_aggregator.AnomalyCorrelator')
    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    def test_stream_io_handling(self, mock_logger_cls, mock_correlator_cls):
        mock_correlator_instance = mock_correlator_cls.return_value
        mock_logger_instance = mock_logger_cls.return_value

        rand_stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=128)).encode('utf-8')
        bio = io.BytesIO(rand_stream_data)

        mock_correlator_instance.correlate_events.return_value = [
            {
                "source": uuid.uuid4().hex,
                "severity": "CRITICAL",
                "details": bio.read().decode('utf-8'),
                "telemetry_snapshot": {}
            }
        ]

        aggregator = AnomalyReportAggregator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            detector=self.rand_detector
        )

        aggregator.aggregate_and_report(uuid.uuid4().hex, random.random())

        mock_logger_instance.log_anomaly.assert_called_once()
        logged_args = mock_logger_instance.log_anomaly.call_args[1]
        self.assertEqual(logged_args["details"], rand_stream_data.decode('utf-8'))

    @patch('skills.anomaly_report_aggregator.AnomalyCorrelator')
    @patch('skills.anomaly_report_aggregator.AnomalyLogger')
    def test_aggregate_and_report_handles_dict_response_and_string_items(self, mock_logger_cls, mock_correlator_cls):
        mock_correlator_instance = mock_correlator_cls.return_value
        mock_logger_instance = mock_logger_cls.return_value

        # Return dict with 'report' list containing mixed types
        mock_correlator_instance.correlate_events.return_value = {
            "correlated_count": 2,
            "report": [
                {"source": "src_1", "severity": "HIGH", "details": {"err": 1}, "telemetry_snapshot": None},
                "src_string_only"
            ]
        }

        aggregator = AnomalyReportAggregator(
            repo_path=self.rand_repo,
            log_path=self.rand_log,
            threshold=self.rand_threshold,
            detector=self.rand_detector
        )

        aggregator.aggregate_and_report("metric_test", 12.34)

        self.assertEqual(mock_logger_instance.log_anomaly.call_count, 2)
        mock_logger_instance.log_anomaly.assert_any_call(
            source="src_1",
            severity="HIGH",
            details={"err": 1},
            telemetry_snapshot=None
        )
        mock_logger_instance.log_anomaly.assert_any_call(
            source="src_string_only",
            severity="UNKNOWN",
            details={},
            telemetry_snapshot=None
        )


if __name__ == '__main__':
    unittest.main()
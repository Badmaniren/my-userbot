import unittest
import uuid
import random
import string
from unittest.mock import MagicMock, patch
from skills.anomaly_report_aggregator import AnomalyReportAggregator, AnomalyReportAggregatorError
from skills.anomaly_correlator import AnomalyCorrelatorError

class TestAnomalyReportAggregator(unittest.TestCase):
    def setUp(self):
        self.random_repo = f"/tmp/repo_{uuid.uuid4().hex}"
        self.random_log = f"/tmp/log_{uuid.uuid4().hex}"
        self.random_threshold = random.uniform(0.1, 0.9)

    def _generate_random_string(self, length=12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_anomaly_data(self):
        return {
            "source": f"source_{uuid.uuid4().hex}",
            "severity": random.choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
            "details": {"msg": self._generate_random_string(20), "code": random.randint(100, 999)},
            "telemetry_snapshot": {self._generate_random_string(5): random.random() for _ in range(3)}
        }

    def test_init_dependency_injection(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        aggregator = AnomalyReportAggregator(
            logger=mock_logger,
            correlator=mock_correlator
        )
        
        self.assertEqual(aggregator.anomaly_logger, mock_logger)
        self.assertEqual(aggregator.correlator, mock_correlator)

    def test_init_default_creation(self):
        with patch('skills.anomaly_report_aggregator.AnomalyLogger') as mock_logger_cls:
            with patch('skills.anomaly_report_aggregator.AnomalyCorrelator') as mock_correlator_cls:
                aggregator = AnomalyReportAggregator(
                    repo_path=self.random_repo,
                    log_path=self.random_log,
                    threshold=self.random_threshold
                )
                mock_logger_cls.assert_called_once_with(log_path=self.random_log)
                mock_correlator_cls.assert_called_once()
                args, kwargs = mock_correlator_cls.call_args
                self.assertEqual(kwargs['repo_path'], self.random_repo)
                self.assertEqual(kwargs['threshold'], self.random_threshold)

    def test_aggregate_and_report_logic_flow(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()
        
        metric_name = f"metric_{uuid.uuid4().hex}"
        metric_value = random.randint(1, 1000)
        
        anomalies = [self._generate_anomaly_data() for _ in range(random.randint(2, 5))]
        mock_correlator.correlate_events.return_value = anomalies

        expected_report = {f"report_{uuid.uuid4().hex}": self._generate_random_string()}
        mock_logger.get_structured_report.return_value = expected_report

        aggregator = AnomalyReportAggregator(logger=mock_logger, correlator=mock_correlator)
        result = aggregator.aggregate_and_report(metric_name, metric_value)

        mock_correlator.correlate_metric.assert_called_once_with(metric_name, metric_value)
        self.assertEqual(mock_logger.log_anomaly.call_count, len(anomalies))

        for i, anomaly in enumerate(anomalies):
            call_args = mock_logger.log_anomaly.call_args_list[i][1]
            self.assertEqual(call_args['source'], anomaly['source'])
            self.assertEqual(call_args['severity'], anomaly['severity'])
            self.assertEqual(call_args['details'], anomaly['details'])
            self.assertEqual(call_args['telemetry_snapshot'], anomaly['telemetry_snapshot'])

        self.assertEqual(result, expected_report)

    def test_aggregate_and_report_exception_handling(self):
        mock_correlator = MagicMock()
        error_msg = f"Correlator failure: {uuid.uuid4().hex}"
        mock_correlator.correlate_metric.side_effect = AnomalyCorrelatorError(error_msg)

        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=MagicMock())

        with self.assertRaises(AnomalyReportAggregatorError) as cm:
            aggregator.aggregate_and_report("any", 0)
        self.assertIn(error_msg, str(cm.exception))

    def test_aggregate_execution_flow_success(self):
        mock_logger = MagicMock()
        mock_correlator = MagicMock()

        exec_id = uuid.uuid4().hex
        payload = {self._generate_random_string(): self._generate_random_string()}

        anomalies = [self._generate_anomaly_data()]
        mock_correlator.analyze_execution_flow.return_value = anomalies

        report_data = {"status": "aggregated", "id": exec_id}
        mock_logger.get_structured_report.return_value = report_data

        aggregator = AnomalyReportAggregator(logger=mock_logger, correlator=mock_correlator)
        result = aggregator.aggregate_execution_flow(exec_id, payload)

        mock_correlator.analyze_execution_flow.assert_called_once_with(exec_id, payload)
        mock_logger.log_anomaly.assert_called_once()
        self.assertEqual(result, report_data)

    def test_aggregate_execution_flow_generic_exception(self):
        mock_correlator = MagicMock()
        random_err = f"Unexpected error {uuid.uuid4().hex}"
        mock_correlator.analyze_execution_flow.side_effect = RuntimeError(random_err)

        aggregator = AnomalyReportAggregator(correlator=mock_correlator, logger=MagicMock())

        with self.assertRaises(AnomalyReportAggregatorError) as cm:
            aggregator.aggregate_execution_flow("id", {})
        self.assertIn(random_err, str(cm.exception))

    def test_generate_final_report_success(self):
        mock_logger = MagicMock()
        final_data = {
            "summary": self._generate_random_string(50),
            "count": random.randint(0, 100),
            "timestamp": uuid.uuid4().hex
        }
        mock_logger.get_structured_report.return_value = final_data

        aggregator = AnomalyReportAggregator(logger=mock_logger, correlator=MagicMock())
        result = aggregator.generate_final_report()

        self.assertEqual(result, final_data)
        mock_logger.get_structured_report.assert_called_once()

    def test_generate_final_report_error(self):
        mock_logger = MagicMock()
        mock_logger.get_structured_report.side_effect = Exception("Logger crash")

        aggregator = AnomalyReportAggregator(logger=mock_logger, correlator=MagicMock())

        with self.assertRaises(AnomalyReportAggregatorError):
            aggregator.generate_final_report()

    def test_backward_compatibility_signatures(self):
        # Проверка наличия всех обязательных методов для anomaly_audit_hub
        aggregator = AnomalyReportAggregator(logger=MagicMock(), correlator=MagicMock())
        self.assertTrue(hasattr(aggregator, 'aggregate_and_report'))
        self.assertTrue(hasattr(aggregator, 'aggregate_execution_flow'))
        self.assertTrue(hasattr(aggregator, 'generate_final_report'))

if __name__ == '__main__':
    unittest.main()
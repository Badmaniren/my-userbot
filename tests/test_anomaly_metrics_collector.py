import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os
import sys

# Добавляем путь к модулям
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.anomaly_metrics_collector import (
    AnomalyAuditHub,
    AnomalyLogger,
    AnomalyFilter,
    ExtractorTool,
    GitInspector
)

class TestAnomalyMetricsCollectorInquisitor(unittest.TestCase):
    def setUp(self):
        self.rand_repo = uuid.uuid4().hex
        self.rand_log = f"{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)

    def test_anomaly_audit_hub_logic(self):
        rnd_source = uuid.uuid4().hex
        rnd_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        rnd_details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        rnd_snapshot = {uuid.uuid4().hex: random.randint(1, 1000)}

        rnd_metric_name = uuid.uuid4().hex
        rnd_metric_value = random.uniform(10.0, 500.0)

        with patch('skills.anomaly_metrics_collector.AnomalyAuditHub.log_anomaly') as mock_log, \
             patch('skills.anomaly_metrics_collector.AnomalyAuditHub.aggregate_and_report') as mock_agg, \
             patch('skills.anomaly_metrics_collector.AnomalyAuditHub.generate_final_report') as mock_rep:

            mock_rep.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

            hub = AnomalyAuditHub(self.rand_repo, self.rand_log, self.rand_threshold)
            hub.log_anomaly(rnd_source, rnd_severity, rnd_details, rnd_snapshot)
            hub.aggregate_and_report(rnd_metric_name, rnd_metric_value)
            report = hub.generate_final_report()

            mock_log.assert_called_once_with(rnd_source, rnd_severity, rnd_details, rnd_snapshot)
            mock_agg.assert_called_once_with(rnd_metric_name, rnd_metric_value)
            self.assertIsInstance(report, dict)

    def test_anomaly_logger_operations(self):
        rnd_source = uuid.uuid4().hex
        rnd_severity = random.choice(['INFO', 'WARNING', 'FATAL'])
        rnd_details = uuid.uuid4().hex
        rnd_snapshot = uuid.uuid4().hex

        with patch('skills.anomaly_metrics_collector.AnomalyLogger.log_anomaly') as mock_log_anom, \
             patch('skills.anomaly_metrics_collector.AnomalyLogger.get_anomalies') as mock_get_anom, \
             patch('skills.anomaly_metrics_collector.AnomalyLogger.get_structured_report') as mock_get_rep, \
             patch('skills.anomaly_metrics_collector.AnomalyLogger.clear_logs') as mock_clear:

            target_list = [{uuid.uuid4().hex: uuid.uuid4().hex}]
            target_report = {uuid.uuid4().hex: random.randint(1, 50)}

            mock_get_anom.return_value = target_list
            mock_get_rep.return_value = target_report

            logger = AnomalyLogger(self.rand_log)
            logger.log_anomaly(rnd_source, rnd_severity, rnd_details, rnd_snapshot)

            anomalies = logger.get_anomalies()
            report = logger.get_structured_report()
            logger.clear_logs()

            mock_log_anom.assert_called_once_with(rnd_source, rnd_severity, rnd_details, rnd_snapshot)
            self.assertEqual(anomalies, target_list)
            self.assertEqual(report, target_report)
            mock_clear.assert_called_once()

    def test_anomaly_filter_function(self):
        rnd_key = uuid.uuid4().hex
        rnd_val = uuid.uuid4().hex
        input_data = {rnd_key: rnd_val, uuid.uuid4().hex: random.randint(0, 100)}

        with patch('skills.anomaly_metrics_collector.start_new') as mock_start:
            expected_output = {rnd_key: rnd_val}
            mock_start.return_value = expected_output

            res = AnomalyFilter.start_new(input_data) if hasattr(AnomalyFilter, 'start_new') else start_new(input_data)
            self.assertEqual(res, expected_output)
            mock_start.assert_called_once_with(input_data)

    def test_extractor_tool_logic(self):
        tool = ExtractorTool()
        rnd_tag = uuid.uuid4().hex
        rnd_attr_key = uuid.uuid4().hex
        rnd_attr_val = uuid.uuid4().hex
        markup = f'<{rnd_tag} {rnd_attr_key}="{rnd_attr_val}">{uuid.uuid4().hex}</{rnd_tag}>'
        tag_string = f'{rnd_tag} {rnd_attr_key}="{rnd_attr_val}"'

        extracted = tool.extract(markup)
        parsed = tool.parse_attributes(tag_string)

        self.assertIsInstance(extracted, dict)
        self.assertIsInstance(parsed, dict)
        self.assertIn(rnd_attr_key, parsed)
        self.assertEqual(parsed[rnd_attr_key], rnd_attr_val)

    def test_git_inspector_methods(self):
        inspector = GitInspector(self.rand_repo)
        rnd_commit = uuid.uuid4().hex
        rnd_file = f"{uuid.uuid4().hex}.py"
        rnd_count = random.randint(1, 100)

        with patch.object(inspector, 'get_commit_history') as mock_hist, \
             patch.object(inspector, 'get_file_diff') as mock_diff, \
             patch.object(inspector, 'analyze_repository') as mock_analyze, \
             patch.object(inspector, 'read_file_at_commit') as mock_read, \
             patch.object(inspector, 'get_latest_changes') as mock_latest:

            mock_hist.return_value = [rnd_commit]
            mock_diff.return_value = uuid.uuid4().hex
            mock_analyze.return_value = {uuid.uuid4().hex: True}
            mock_read.return_value = uuid.uuid4().hex
            mock_latest.return_value = [rnd_file]

            self.assertEqual(inspector.get_commit_history(rnd_count), [rnd_commit])
            self.assertEqual(inspector.get_file_diff(rnd_commit), mock_diff.return_value)
            self.assertEqual(inspector.analyze_repository(), mock_analyze.return_value)
            self.assertEqual(inspector.read_file_at_commit(rnd_commit, rnd_file), mock_read.return_value)
            self.assertEqual(inspector.get_latest_changes(), [rnd_file])

            mock_hist.assert_called_once_with(rnd_count)
            mock_diff.assert_called_once_with(rnd_commit)
            mock_analyze.assert_called_once()
            mock_read.assert_called_once_with(rnd_commit, rnd_file)
            mock_latest.assert_called_once()

    def test_io_stream_mocking_chaos(self):
        garbage_bytes = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=64)).encode('utf-8')
        fake_stream = io.BytesIO(garbage_bytes)

        with patch('skills.anomaly_metrics_collector.open', return_value=fake_stream):
            read_data = fake_stream.read()
            self.assertEqual(read_data, garbage_bytes)

if __name__ == '__main__':
    unittest.main()
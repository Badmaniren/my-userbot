import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os
import sys

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.anomaly_diagnostic_profiler import (
    AnomalyAuditHub,
    AnomalyLogger,
    ExtractorTool,
    GitInspector
)

class TestAnomalyDiagnosticProfiler(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.threshold = random.uniform(0.1, 99.9)

    def test_anomaly_audit_hub_workflow(self):
        rand_source = uuid.uuid4().hex
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(3)}
        rand_telemetry = {uuid.uuid4().hex: random.random() for _ in range(2)}
        rand_metric = uuid.uuid4().hex
        rand_value = random.uniform(1.0, 1000.0)

        with patch('skills.anomaly_diagnostic_profiler.AnomalyAuditHub.log_anomaly') as mock_log, \
             patch('skills.anomaly_diagnostic_profiler.AnomalyAuditHub.aggregate_and_report') as mock_agg, \
             patch('skills.anomaly_diagnostic_profiler.AnomalyAuditHub.generate_final_report') as mock_rep:

            mock_rep.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

            hub = AnomalyAuditHub(self.rand_repo, self.rand_log, self.threshold)
            hub.log_anomaly(rand_source, rand_severity, rand_details, rand_telemetry)
            hub.aggregate_and_report(rand_metric, rand_value)
            report = hub.generate_final_report()

            mock_log.assert_called_once_with(rand_source, rand_severity, rand_details, rand_telemetry)
            mock_agg.assert_called_once_with(rand_metric, rand_value)
            self.assertIsInstance(report, dict)

    def test_anomaly_logger_operations(self):
        rand_source = uuid.uuid4().hex
        rand_severity = random.choice(["INFO", "WARNING", "FATAL"])
        rand_details = uuid.uuid4().hex
        rand_telemetry = [random.randint(0, 100) for _ in range(5)]

        logger = AnomalyLogger(self.rand_log)

        with patch.object(logger, 'log_anomaly', return_value=None) as mock_log_anom, \
             patch.object(logger, 'get_anomalies', return_value=[{"source": rand_source}]) as mock_get_anom, \
             patch.object(logger, 'get_structured_report', return_value={uuid.uuid4().hex: uuid.uuid4().hex}) as mock_rep, \
             patch.object(logger, 'clear_logs', return_value=True) as mock_clear:

            logger.log_anomaly(rand_source, rand_severity, rand_details, rand_telemetry)
            mock_log_anom.assert_called_once_with(rand_source, rand_severity, rand_details, rand_telemetry)

            anomalies = logger.get_anomalies()
            self.assertEqual(anomalies[0]["source"], rand_source)

            report = logger.get_structured_report()
            self.assertTrue(len(report) > 0)

            res = logger.clear_logs()
            self.assertTrue(res)

    def test_extractor_tool_markup(self):
        extractor = ExtractorTool()
        rand_tag = uuid.uuid4().hex
        rand_attr_key = uuid.uuid4().hex
        rand_attr_val = uuid.uuid4().hex
        markup = f"<{rand_tag} {rand_attr_key}=\"{rand_attr_val}\">Some text</{rand_tag}>"

        with patch.object(extractor, 'extract') as mock_extract, \
             patch.object(extractor, 'parse_attributes') as mock_parse:

            mock_extract.return_value = {rand_attr_key: rand_attr_val}
            mock_parse.return_value = {rand_attr_key: rand_attr_val}

            extracted = extractor.extract(markup)
            self.assertEqual(extracted[rand_attr_key], rand_attr_val)

            parsed = extractor.parse_attributes(f"{rand_attr_key}=\"{rand_attr_val}\"")
            self.assertEqual(parsed[rand_attr_key], rand_attr_val)

    def test_git_inspector_methods(self):
        inspector = GitInspector(self.rand_repo)
        rand_commit = uuid.uuid4().hex[:8]
        rand_file = f"{uuid.uuid4().hex}.py"
        max_count = random.randint(1, 50)

        with patch.object(inspector, 'get_commit_history', return_value=[rand_commit]) as mock_hist, \
             patch.object(inspector, 'get_file_diff', return_value=uuid.uuid4().hex) as mock_diff, \
             patch.object(inspector, 'read_file_at_commit', return_value=uuid.uuid4().hex) as mock_read, \
             patch.object(inspector, 'analyze_repository', return_value={uuid.uuid4().hex: random.randint(1, 10)}) as mock_analyze:

            history = inspector.get_commit_history(max_count)
            self.assertIn(rand_commit, history)

            diff = inspector.get_file_diff(rand_commit)
            self.assertIsInstance(diff, str)

            file_content = inspector.read_file_at_commit(rand_commit, rand_file)
            self.assertIsInstance(file_content, str)

            analysis = inspector.analyze_repository()
            self.assertIsInstance(analysis, dict)

if __name__ == '__main__':
    unittest.main()
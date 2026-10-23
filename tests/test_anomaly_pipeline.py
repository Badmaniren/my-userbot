import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.anomaly_pipeline import (
    AnomalyAuditHub,
    AnomalyLogger,
    start_new,
    ExtractorTool,
    GitInspector
)

class TestAnomalyPipelineInquisitor(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_log = f"/tmp/{uuid.uuid4().hex}.log"
        self.rand_threshold = random.uniform(0.1, 99.9)
        self.hub = AnomalyAuditHub(self.rand_repo, self.rand_log, self.rand_threshold)
        self.logger = AnomalyLogger(self.rand_log)
        self.extractor = ExtractorTool()

    def test_anomaly_audit_hub_initialization(self):
        rand_repo_val = f"/repo/{uuid.uuid4().hex}"
        rand_log_val = f"/var/log/{uuid.uuid4().hex}.log"
        rand_thresh_val = random.randint(1, 100)
        
        hub_instance = AnomalyAuditHub(rand_repo_val, rand_log_val, rand_thresh_val)
        self.assertEqual(hub_instance.repo_path, rand_repo_val)
        self.assertEqual(hub_instance.log_path, rand_log_val)
        self.assertEqual(hub_instance.threshold, rand_thresh_val)

    def test_anomaly_audit_hub_log_and_aggregate(self):
        rand_source = ''.join(random.choices(string.ascii_lowercase, k=10))
        rand_severity = random.choice(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_telemetry = {uuid.uuid4().hex: random.random()}
        
        metric_name = uuid.uuid4().hex
        metric_value = random.uniform(10.0, 500.0)

        with patch.object(self.hub, 'log_anomaly') as mock_log:
            self.hub.log_anomaly(rand_source, rand_severity, rand_details, rand_telemetry)
            mock_log.assert_called_once_with(rand_source, rand_severity, rand_details, rand_telemetry)

        with patch.object(self.hub, 'aggregate_and_report', return_value=True) as mock_agg:
            res = self.hub.aggregate_and_report(metric_name, metric_value)
            self.assertTrue(res)
            mock_agg.assert_called_once_with(metric_name, metric_value)

    def test_anomaly_audit_hub_generate_final_report(self):
        rand_report_id = uuid.uuid4().hex
        with patch.object(self.hub, 'generate_final_report', return_value={'report_id': rand_report_id}) as mock_rep:
            report = self.hub.generate_final_report()
            self.assertEqual(report['report_id'], rand_report_id)
            mock_rep.assert_called_once()

    def test_anomaly_logger_operations(self):
        rand_source = uuid.uuid4().hex
        rand_severity = uuid.uuid4().hex
        rand_details = {uuid.uuid4().hex: uuid.uuid4().hex}
        rand_telemetry = {uuid.uuid4().hex: uuid.uuid4().hex}

        self.logger.clear_logs()
        self.assertEqual(len(self.logger.get_anomalies()), 0)

        self.logger.log_anomaly(rand_source, rand_severity, rand_details, rand_telemetry)
        anomalies = self.logger.get_anomalies()
        self.assertGreaterEqual(len(anomalies), 1)
        
        found = False
        for anomaly in anomalies:
            if anomaly.get('source') == rand_source:
                found = True
                self.assertEqual(anomaly.get('severity'), rand_severity)
        self.assertTrue(found)

        structured = self.logger.get_structured_report()
        self.assertIsInstance(structured, (dict, list, str))

    def test_anomaly_filter_start_new(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        input_data = {rand_key: rand_val, 'risk_score': random.randint(50, 100)}

        with patch('skills.anomaly_pipeline.start_new') as mock_start:
            mock_start.return_value = {rand_key: rand_val, 'filtered': True}
            result = start_new(input_data)
            self.assertTrue(result['filtered'])
            self.assertEqual(result[rand_key], rand_val)
            mock_start.assert_called_once_with(input_data)

    def test_extractor_tool_parse_and_extract(self):
        rand_tag_key = uuid.uuid4().hex
        rand_tag_val = uuid.uuid4().hex
        rand_markup = f"<{uuid.uuid4().hex} {rand_tag_key}='{rand_tag_val}'>{uuid.uuid4().hex}</{uuid.uuid4().hex}>"
        
        tag_string_key = uuid.uuid4().hex
        tag_string_val = uuid.uuid4().hex
        tag_string = f'{tag_string_key}="{tag_string_val}"'

        parsed_attrs = self.extractor.parse_attributes(tag_string)
        self.assertIn(tag_string_key, parsed_attrs)
        self.assertEqual(parsed_attrs[tag_string_key], tag_string_val)

        extraction_result = self.extractor.extract(rand_markup)
        self.assertIsInstance(extraction_result, dict)

    def test_git_inspector_operations(self):
        inspector = GitInspector(self.rand_repo)
        rand_commit = uuid.uuid4().hex
        rand_file = f"src/{uuid.uuid4().hex}.py"
        rand_count = random.randint(1, 50)

        with patch.object(inspector, 'get_commit_history', return_value=[{'commit': rand_commit}]) as mock_hist:
            history = inspector.get_commit_history(max_count=rand_count)
            self.assertEqual(history[0]['commit'], rand_commit)
            mock_hist.assert_called_once_with(max_count=rand_count)

        with patch.object(inspector, 'read_file_at_commit', return_value=b"random_file_content") as mock_read:
            content = inspector.read_file_at_commit(rand_commit, rand_file)
            self.assertEqual(content, b"random_file_content")
            mock_read.assert_called_once_with(rand_commit, rand_file)

        with patch.object(inspector, 'analyze_repository', return_value={'status': 'clean'}) as mock_an:
            analysis = inspector.analyze_repository()
            self.assertEqual(analysis['status'], 'clean')
            mock_an.assert_called_once()

    def test_chaos_io_bytes_handling(self):
        rand_garbage = f"ERROR_CODE_{uuid.uuid4().hex}".encode('utf-8')
        mock_file_stream = io.BytesIO(rand_garbage)

        with patch('skills.anomaly_pipeline.open', return_value=mock_file_stream, create=True):
            read_data = mock_file_stream.read()
            self.assertEqual(read_data, rand_garbage)

if __name__ == '__main__':
    unittest.main()
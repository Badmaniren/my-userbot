import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import os

from skills.repo_audit_collector import RepoAuditCollector

class TestRepoAuditCollector(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.output_dir = f"/tmp/out_{uuid.uuid4().hex}"
        self.collector = RepoAuditCollector(self.repo_path, self.output_dir)

    @patch('skills.repo_audit_collector.RepoAuditor')
    @patch('skills.repo_audit_collector.RepoAuditSynthesizer')
    def test_collect_and_aggregate_success(self, mock_synthesizer_class, mock_auditor_class):
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(100, 9999)
        rand_issue = uuid.uuid4().hex
        
        mock_auditor_instance = mock_auditor_class.return_value
        mock_auditor_instance.calculate_metrics.return_value = {rand_metric_key: rand_metric_val}
        mock_auditor_instance.detect_issues.return_value = [rand_issue]
        mock_auditor_instance.analyze_structure.return_value = {uuid.uuid4().hex: uuid.uuid4().hex}

        rand_synthesis_key = uuid.uuid4().hex
        rand_synthesis_val = uuid.uuid4().hex
        mock_synthesizer_instance = mock_synthesizer_class.return_value
        mock_synthesizer_instance.synthesize.return_value = {rand_synthesis_key: rand_synthesis_val}

        rand_export_path = f"/tmp/{uuid.uuid4().hex}.json"
        mock_synthesizer_instance.export_report.return_value = rand_export_path

        result = self.collector.collect_and_aggregate()

        mock_auditor_class.assert_called_once_with(self.repo_path)
        mock_auditor_instance.calculate_metrics.assert_called_once()
        mock_auditor_instance.detect_issues.assert_called_once()
        mock_auditor_instance.analyze_structure.assert_called_once()

        mock_synthesizer_class.assert_called_once()
        mock_synthesizer_instance.synthesize.assert_called_once()
        mock_synthesizer_instance.export_report.assert_called_once()

        self.assertIn(rand_metric_key, result['metrics'])
        self.assertEqual(result['metrics'][rand_metric_key], rand_metric_val)
        self.assertIn(rand_issue, result['issues'])
        self.assertIn(rand_synthesis_key, result['synthesis'])
        self.assertEqual(result['synthesis'][rand_synthesis_key], rand_synthesis_val)
        self.assertEqual(result['export_path'], rand_export_path)

    @patch('skills.repo_audit_collector.RepoAuditor')
    def test_collect_metrics_failure_handling(self, mock_auditor_class):
        rand_error_msg = f"Error_{uuid.uuid4().hex}"
        mock_auditor_instance = mock_auditor_class.return_value
        mock_auditor_instance.calculate_metrics.side_effect = Exception(rand_error_msg)

        with self.assertRaises(Exception) as ctx:
            self.collector.collect_metrics()

        self.assertIn(rand_error_msg, str(ctx.exception))

    @patch('skills.repo_audit_collector.start_new')
    def test_start_new_wrapper(self, mock_start_new):
        rand_stream_content = uuid.uuid4().bytes
        mock_stream = io.BytesIO(rand_stream_content)
        
        rand_return_val = uuid.uuid4().hex
        mock_start_new.return_value = rand_return_val

        res = self.collector.run_external_synthesizer(mock_stream)

        mock_start_new.assert_called_once_with(self.repo_path, self.output_dir, mock_stream)
        self.assertEqual(res, rand_return_val)

    @patch('skills.repo_audit_collector.RepoAuditor')
    def test_process_stream_integration(self, mock_auditor_class):
        rand_stream_data = f"data_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)

        rand_output = uuid.uuid4().hex
        mock_auditor_instance = mock_auditor_class.return_value
        mock_auditor_instance.process_log_stream.return_value = rand_output

        res = self.collector.process_audit_stream(mock_stream)

        mock_auditor_instance.process_log_stream.assert_called_once_with(mock_stream)
        self.assertEqual(res, rand_output)

if __name__ == '__main__':
    unittest.main()
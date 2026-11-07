import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import os
from skills.repo_audit_collector import RepoAuditCollector, start_new

class TestRepoAuditCollector(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.output_dir = f"/tmp/{uuid.uuid4().hex}"
        self.collector = RepoAuditCollector(repository_path=self.repo_path, output_dir=self.output_dir)

    @patch('skills.repo_audit_collector.RepoAuditor')
    @patch('skills.repo_audit_collector.RepoAuditSynthesizer')
    def test_collect_and_aggregate_success(self, mock_synthesizer_cls, mock_auditor_cls):
        mock_auditor = mock_auditor_cls.return_value
        mock_synthesizer = mock_synthesizer_cls.return_value

        expected_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_issues = [uuid.uuid4().hex, uuid.uuid4().hex]
        expected_structure = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_synthesis = {uuid.uuid4().hex: random.random()}
        expected_export_path = f"/tmp/{uuid.uuid4().hex}.json"

        mock_auditor.calculate_metrics.return_value = expected_metrics
        mock_auditor.detect_issues.return_value = expected_issues
        mock_auditor.analyze_structure.return_value = expected_structure
        mock_synthesizer.synthesize.return_value = expected_synthesis
        mock_synthesizer.export_report.return_value = expected_export_path

        collector = RepoAuditCollector(repository_path=self.repo_path, output_dir=self.output_dir)
        result = collector.collect_and_aggregate()

        self.assertEqual(result["metrics"], expected_metrics)
        self.assertEqual(result["issues"], expected_issues)
        self.assertEqual(result["structure"], expected_structure)
        self.assertEqual(result["synthesis"], expected_synthesis)
        self.assertEqual(result["export_path"], expected_export_path)
        self.assertEqual(result["audit_metrics"], expected_metrics)
        self.assertEqual(result["synthesis_result"], expected_synthesis)

        mock_auditor.calculate_metrics.assert_called_once()
        mock_auditor.detect_issues.assert_called_once()
        mock_auditor.analyze_structure.assert_called_once()
        mock_synthesizer.synthesize.assert_called_once_with({
            "metrics": expected_metrics,
            "issues": expected_issues,
            "structure": expected_structure
        })
        mock_synthesizer.export_report.assert_called_once_with(self.output_dir, expected_synthesis, "report.json")

    @patch('skills.repo_audit_collector.RepoAuditor')
    def test_collect_metrics_failure_handling(self, mock_auditor_cls):
        mock_auditor = mock_auditor_cls.return_value
        random_error_message = uuid.uuid4().hex
        mock_auditor.calculate_metrics.side_effect = RuntimeError(random_error_message)

        collector = RepoAuditCollector(repository_path=self.repo_path, output_dir=self.output_dir)
        with self.assertRaises(RuntimeError) as ctx:
            collector.collect_metrics()

        self.assertIn(random_error_message, str(ctx.exception))

    @patch('skills.repo_audit_collector.RepoAuditor')
    def test_process_stream_integration(self, mock_auditor_cls):
        mock_auditor = mock_auditor_cls.return_value
        random_stream_data = uuid.uuid4().bytes
        random_stream_result = uuid.uuid4().hex
        mock_auditor.process_log_stream.return_value = random_stream_result

        stream = io.BytesIO(random_stream_data)
        collector = RepoAuditCollector(repository_path=self.repo_path, output_dir=self.output_dir)
        result = collector.process_audit_stream(stream)

        self.assertEqual(result, random_stream_result)
        mock_auditor.process_log_stream.assert_called_once_with(stream)

    @patch('skills.repo_audit_collector.start_new')
    def test_run_external_synthesizer(self, mock_start_new):
        random_stream_data = uuid.uuid4().bytes
        random_return_value = uuid.uuid4().hex
        mock_start_new.return_value = random_return_value

        stream = io.BytesIO(random_stream_data)
        collector = RepoAuditCollector(repository_path=self.repo_path, output_dir=self.output_dir)
        result = collector.run_external_synthesizer(stream)

        self.assertEqual(result, random_return_value)
        mock_start_new.assert_called_once_with(self.repo_path, self.output_dir, stream)

    @patch('skills.repo_audit_collector.RepoAuditor')
    @patch('skills.repo_audit_collector.RepoAuditSynthesizer')
    def test_export_aggregated_report(self, mock_synthesizer_cls, mock_auditor_cls):
        mock_auditor = mock_auditor_cls.return_value
        mock_synthesizer = mock_synthesizer_cls.return_value

        mock_auditor.calculate_metrics.return_value = {}
        mock_auditor.detect_issues.return_value = []
        mock_auditor.analyze_structure.return_value = {}
        mock_synthesizer.synthesize.return_value = {}

        random_filename = f"{uuid.uuid4().hex}.json"
        random_export_path = f"/tmp/{uuid.uuid4().hex}"
        mock_synthesizer.export_report.return_value = random_export_path

        collector = RepoAuditCollector(repository_path=self.repo_path, output_dir=self.output_dir)
        path = collector.export_aggregated_report(filename=random_filename)

        self.assertEqual(path, random_export_path)
        mock_synthesizer.export_report.assert_called_once_with(self.output_dir, {}, random_filename)
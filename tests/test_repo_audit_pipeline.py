import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.repo_audit_pipeline import RepoAuditPipeline, run_audit_pipeline

class TestRepoAuditPipeline(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.output_dir = f"/tmp/out_{uuid.uuid4().hex}"
        self.export_stream_path = f"/tmp/stream_{uuid.uuid4().hex}"

    @patch('skills.repo_audit_pipeline.RepoAuditor')
    @patch('skills.repo_audit_pipeline.RepoAuditSynthesizer')
    def test_pipeline_initialization_and_execution(self, mock_synthesizer_cls, mock_auditor_cls):
        mock_auditor_instance = mock_auditor_cls.return_value
        mock_synthesizer_instance = mock_synthesizer_cls.return_value

        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.randint(100, 999)
        audit_mock_data = {random_metric_key: random_metric_val}
        mock_auditor_instance.audit_repository.return_value = audit_mock_data

        random_synthesis_key = uuid.uuid4().hex
        random_synthesis_val = uuid.uuid4().hex
        synthesis_mock_data = {random_synthesis_key: random_synthesis_val}
        mock_synthesizer_instance.synthesize.return_value = synthesis_mock_data

        export_stream = io.StringIO()
        pipeline = RepoAuditPipeline(
            repository_path=self.repo_path,
            output_dir=self.output_dir,
            export_stream=export_stream
        )

        mock_auditor_cls.assert_called_once_with(self.repo_path)
        mock_synthesizer_cls.assert_called_once()

        result = pipeline.execute()

        mock_auditor_instance.audit_repository.assert_called_once()
        mock_synthesizer_instance.synthesize.assert_called_once_with(audit_mock_data)

        if hasattr(mock_synthesizer_instance, "export_report"):
            try:
                mock_synthesizer_instance.export_report.assert_called_once_with(synthesis_mock_data, export_stream)
            except TypeError:
                mock_synthesizer_instance.export_report.assert_called_once_with(export_stream)
        elif hasattr(mock_synthesizer_instance, "export"):
            mock_synthesizer_instance.export.assert_called_once_with(export_stream)

        self.assertEqual(result, synthesis_mock_data)

    @patch('skills.repo_audit_pipeline.RepoAuditor')
    @patch('skills.repo_audit_pipeline.RepoAuditSynthesizer')
    def test_pipeline_fallback_methods_in_auditor(self, mock_synthesizer_cls, mock_auditor_cls):
        mock_auditor_instance = mock_auditor_cls.return_value
        mock_synthesizer_instance = mock_synthesizer_cls.return_value

        del mock_auditor_instance.audit_repository
        del mock_auditor_instance.audit

        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.randint(1, 99)
        mock_auditor_instance.calculate_metrics.return_value = {random_metric_key: random_metric_val}

        synthesis_mock_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_synthesizer_instance.synthesize.return_value = synthesis_mock_data

        pipeline = RepoAuditPipeline(repository_path=self.repo_path)
        result = pipeline.execute()

        mock_auditor_instance.calculate_metrics.assert_called_once()
        mock_synthesizer_instance.synthesize.assert_called_once()
        self.assertEqual(result, synthesis_mock_data)

    @patch('skills.repo_audit_pipeline.RepoAuditor')
    @patch('skills.repo_audit_pipeline.RepoAuditSynthesizer')
    def test_process_stream_sets_export_stream(self, mock_synthesizer_cls, mock_auditor_cls):
        mock_auditor_instance = mock_auditor_cls.return_value
        mock_synthesizer_instance = mock_synthesizer_cls.return_value

        audit_data = {uuid.uuid4().hex: random.randint(10, 50)}
        mock_auditor_instance.audit.return_value = audit_data

        synthesis_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_synthesizer_instance.synthesize.return_value = synthesis_data

        pipeline = RepoAuditPipeline(repository_path=self.repo_path, output_dir=self.output_dir)
        self.assertIsNone(pipeline.export_stream)

        stream = io.BytesIO(uuid.uuid4().bytes)
        pipeline.process_stream(stream)
        self.assertEqual(pipeline.export_stream, stream)

        result = pipeline.execute()
        self.assertEqual(result, synthesis_data)

        if hasattr(mock_synthesizer_instance, "export_report"):
            try:
                mock_synthesizer_instance.export_report.assert_called_once_with(synthesis_data, stream)
            except TypeError:
                mock_synthesizer_instance.export_report.assert_called_once_with(stream)

    @patch('skills.repo_audit_pipeline.RepoAuditor')
    @patch('skills.repo_audit_pipeline.RepoAuditSynthesizer')
    def test_run_audit_pipeline_functional_wrapper(self, mock_synthesizer_cls, mock_auditor_cls):
        mock_auditor_instance = mock_auditor_cls.return_value
        mock_synthesizer_instance = mock_synthesizer_cls.return_value

        audit_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_auditor_instance.audit_repository.return_value = audit_data

        expected_synthesis = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_synthesizer_instance.synthesize.return_value = expected_synthesis

        export_stream = io.StringIO()
        result = run_audit_pipeline(
            repository_path=self.repo_path,
            output_dir=self.output_dir,
            export_stream=export_stream
        )

        mock_auditor_cls.assert_called_once_with(self.repo_path)
        mock_synthesizer_cls.assert_called_once()
        mock_auditor_instance.audit_repository.assert_called_once()
        mock_synthesizer_instance.synthesize.assert_called_once_with(audit_data)
        self.assertEqual(result, expected_synthesis)

if __name__ == '__main__':
    unittest.main()
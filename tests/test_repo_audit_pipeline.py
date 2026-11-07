import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.repo_audit_pipeline import (
    run_audit_pipeline,
    RepoAuditPipeline
)

class TestRepoAuditPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo_path = f"/path/to/repo_{uuid.uuid4().hex[:8]}"
        self.rand_output_dir = f"/path/to/output_{uuid.uuid4().hex[:8]}"
        self.rand_stream_data = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        self.rand_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.rand_metric_val = random.randint(100, 999)
        self.rand_synthesis_key = f"synthesis_{uuid.uuid4().hex[:6]}"
        self.rand_synthesis_val = f"val_{uuid.uuid4().hex[:6]}"

    def test_pipeline_composition_and_execution(self):
        mock_audit_result = {self.rand_metric_key: self.rand_metric_val}
        mock_synthesis_result = {self.rand_synthesis_key: self.rand_synthesis_val}

        with patch("skills.repo_audit_pipeline.RepoAuditor") as mock_auditor_cls, \
             patch("skills.repo_audit_pipeline.RepoAuditSynthesizer") as mock_synth_cls:

            instance_auditor = mock_auditor_cls.return_value
            instance_auditor.audit_repository.return_value = mock_audit_result

            instance_synth = mock_synth_cls.return_value
            instance_synth.synthesize.return_value = mock_synthesis_result

            stream = io.BytesIO(self.rand_stream_data)
            pipeline = RepoAuditPipeline(
                repository_path=self.rand_repo_path,
                output_dir=self.rand_output_dir,
                export_stream=stream
            )
            result = pipeline.execute()

            mock_auditor_cls.assert_called_once_with(self.rand_repo_path)
            instance_auditor.audit_repository.assert_called_once()

            instance_synth.synthesize.assert_called_once_with(mock_audit_result)
            instance_synth.export_report.assert_called()

            self.assertEqual(result, mock_synthesis_result)

    def test_functional_pipeline_wrapper(self):
        mock_audit_result = {self.rand_metric_key: self.rand_metric_val}
        mock_synthesis_result = {self.rand_synthesis_key: self.rand_synthesis_val}

        with patch("skills.repo_audit_pipeline.RepoAuditor") as mock_auditor_cls, \
             patch("skills.repo_audit_pipeline.RepoAuditSynthesizer") as mock_synth_cls:

            instance_auditor = mock_auditor_cls.return_value
            instance_auditor.audit.return_value = mock_audit_result

            instance_synth = mock_synth_cls.return_value
            instance_synth.synthesize.return_value = mock_synthesis_result

            stream = io.BytesIO(self.rand_stream_data)
            output = run_audit_pipeline(
                repository_path=self.rand_repo_path,
                output_dir=self.rand_output_dir,
                export_stream=stream
            )

            self.assertIsInstance(output, dict)
            self.assertIn(self.rand_synthesis_key, output)
            self.assertEqual(output[self.rand_synthesis_key], self.rand_synthesis_val)

    def test_pipeline_handles_stream_and_custom_methods(self):
        with patch("skills.repo_audit_pipeline.RepoAuditor") as mock_auditor_cls, \
             patch("skills.repo_audit_pipeline.RepoAuditSynthesizer") as mock_synth_cls:

            instance_auditor = mock_auditor_cls.return_value
            instance_auditor.calculate_metrics.return_value = {self.rand_metric_key: self.rand_metric_val}

            instance_synth = mock_synth_cls.return_value
            instance_synth.synthesize.return_value = {self.rand_synthesis_key: self.rand_synthesis_val}

            stream = io.BytesIO(self.rand_stream_data)
            pipeline = RepoAuditPipeline(
                repository_path=self.rand_repo_path,
                output_dir=self.rand_output_dir,
                export_stream=stream
            )

            if hasattr(pipeline, "process_stream"):
                pipeline.process_stream(stream)

            metrics = instance_auditor.calculate_metrics()
            self.assertEqual(metrics[self.rand_metric_key], self.rand_metric_val)

if __name__ == "__main__":
    unittest.main()
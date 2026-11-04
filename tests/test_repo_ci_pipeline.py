import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.repo_ci_pipeline import RepoCIPipeline

class TestRepoCIPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex}"

    def test_pipeline_initialization(self):
        pipeline = RepoCIPipeline(self.rand_repo)
        self.assertEqual(pipeline.repo_path, self.rand_repo)

    @patch('skills.repo_ci_pipeline.RepoAuditor')
    @patch('skills.repo_ci_pipeline.RepoTagger')
    def test_run_ci_pipeline_success(self, mock_tagger_cls, mock_auditor_cls):
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 100)
        rand_version = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

        mock_auditor_instance = mock_auditor_cls.return_value
        mock_auditor_instance.audit.return_value = True
        mock_auditor_instance.detect_issues.return_value = []
        mock_auditor_instance.calculate_metrics.return_value = {rand_metric_key: rand_metric_val}

        mock_tagger_instance = mock_tagger_cls.return_value
        mock_tagger_instance.evaluate_release_readiness.return_value = True
        mock_tagger_instance.determine_next_version.return_value = rand_version
        mock_tagger_instance.apply_and_push_tag.return_value = True

        pipeline = RepoCIPipeline(self.rand_repo)
        result = pipeline.run_pipeline()

        self.assertTrue(result)
        mock_auditor_instance.audit.assert_called_once()
        mock_tagger_instance.evaluate_release_readiness.assert_called_once()
        mock_tagger_instance.apply_and_push_tag.assert_called_once_with(rand_version)

    @patch('skills.repo_ci_pipeline.RepoAuditor')
    @patch('skills.repo_ci_pipeline.RepoTagger')
    def test_run_ci_pipeline_audit_failure(self, mock_tagger_cls, mock_auditor_cls):
        rand_issue = f"issue_{uuid.uuid4().hex}"

        mock_auditor_instance = mock_auditor_cls.return_value
        mock_auditor_instance.audit.return_value = False
        mock_auditor_instance.detect_issues.return_value = [rand_issue]

        mock_tagger_instance = mock_tagger_cls.return_value

        pipeline = RepoCIPipeline(self.rand_repo)
        result = pipeline.run_pipeline()

        self.assertFalse(result)
        mock_auditor_instance.audit.assert_called_once()
        mock_tagger_instance.evaluate_release_readiness.assert_not_called()

    @patch('skills.repo_ci_pipeline.RepoAuditor')
    @patch('skills.repo_ci_pipeline.RepoTagger')
    def test_run_ci_pipeline_tagging_failure(self, mock_tagger_cls, mock_auditor_cls):
        rand_version = f"v{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

        mock_auditor_instance = mock_auditor_cls.return_value
        mock_auditor_instance.audit.return_value = True
        mock_auditor_instance.detect_issues.return_value = []

        mock_tagger_instance = mock_tagger_cls.return_value
        mock_tagger_instance.evaluate_release_readiness.return_value = True
        mock_tagger_instance.determine_next_version.return_value = rand_version
        mock_tagger_instance.apply_and_push_tag.return_value = False

        pipeline = RepoCIPipeline(self.rand_repo)
        result = pipeline.run_pipeline()

        self.assertFalse(result)
        mock_tagger_instance.apply_and_push_tag.assert_called_once_with(rand_version)

    @patch('skills.repo_ci_pipeline.RepoAuditor')
    def test_process_stream_audit(self, mock_auditor_cls):
        rand_stream_data = f"stream_payload_{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(rand_stream_data)

        rand_result_string = f"result_{uuid.uuid4().hex}"

        mock_auditor_instance = mock_auditor_cls.return_value
        mock_auditor_instance.process_stream.return_value = rand_result_string

        pipeline = RepoCIPipeline(self.rand_repo)
        res = pipeline.process_audit_stream(mock_stream)

        self.assertEqual(res, rand_result_string)
        mock_auditor_instance.process_stream.assert_called_once_with(mock_stream)

if __name__ == '__main__':
    unittest.main()
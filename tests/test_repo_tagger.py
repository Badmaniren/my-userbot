import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os

from skills.repo_tagger import (
    RepoTagger,
    RepoMetricsCollector,
    ReleaseAuditor,
    TagManager
)


class TestRepoTaggerSystem(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"

    def test_repo_tagger_initialization_and_evaluation(self):
        rand_prefix = ''.join(random.choices(string.ascii_lowercase, k=6))
        tagger = RepoTagger(self.repo_path)
        
        self.assertEqual(tagger.repo_path, self.repo_path)
        
        with patch('skills.repo_tagger.RepoTagger._evaluate_readiness') as mock_eval:
            expected_flag = random.choice([True, False])
            mock_eval.return_value = expected_flag
            
            result = tagger.evaluate_release_readiness()
            self.assertEqual(result, expected_flag)
            mock_eval.assert_called_once()

    def test_metrics_collector_processing_stream(self):
        collector = RepoMetricsCollector(self.repo_path)
        
        metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        metric_val = random.randint(100, 9999)
        raw_stream = f"{metric_key}:{metric_val}\n".encode('utf-8')
        stream_mock = io.BytesIO(raw_stream)
        
        metrics = collector.process_metrics_stream(stream_mock)
        
        self.assertIsInstance(metrics, dict)
        self.assertIn(metric_key, metrics)
        self.assertEqual(metrics[metric_key], metric_val)

    def test_release_auditor_check_stability(self):
        auditor = ReleaseAuditor(self.repo_path)
        
        score_threshold = random.uniform(50.0, 95.0)
        mock_metrics = {
            f"metric_{uuid.uuid4().hex[:4]}": random.uniform(score_threshold, 100.0)
            for _ in range(3)
        }
        
        with patch.object(auditor, 'calculate_stability_index', return_value=score_threshold + 5.0) as mock_calc:
            is_stable = auditor.audit_stability(mock_metrics)
            self.assertTrue(is_stable)
            mock_calc.assert_called_once_with(mock_metrics)

    def test_tag_manager_apply_tag(self):
        tag_manager = TagManager(self.repo_path)
        
        major = random.randint(1, 5)
        minor = random.randint(0, 9)
        patch_ver = random.randint(0, 20)
        generated_tag = f"v{major}.{minor}.{patch_ver}"
        
        with patch('skills.repo_tagger.subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = f"tagged_{uuid.uuid4().hex}".encode('utf-8')
            
            success = tag_manager.create_release_tag(generated_tag)
            
            self.assertTrue(success)
            mock_run.assert_called()
            called_args = mock_run.call_args[0][0]
            self.assertIn(generated_tag, called_args)

    def test_repo_tagger_full_workflow_success(self):
        tagger = RepoTagger(self.repo_path)
        version_str = f"v{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        with patch.object(tagger, 'evaluate_release_readiness', return_value=True), \
             patch.object(tagger, 'determine_next_version', return_value=version_str), \
             patch.object(tagger, 'apply_and_push_tag', return_value=True) as mock_apply:
            
            execution_status = tagger.run_auto_tagging()
            
            self.assertTrue(execution_status)
            mock_apply.assert_called_once_with(version_str)

    def test_repo_tagger_full_workflow_failure_on_readiness(self):
        tagger = RepoTagger(self.repo_path)
        
        with patch.object(tagger, 'evaluate_release_readiness', return_value=False), \
             patch.object(tagger, 'apply_and_push_tag') as mock_apply:
            
            execution_status = tagger.run_auto_tagging()
            
            self.assertFalse(execution_sats := execution_status)
            mock_apply.assert_not_called()


if __name__ == '__main__':
    unittest.main()
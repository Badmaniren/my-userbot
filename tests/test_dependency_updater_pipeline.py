import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.dependency_updater_pipeline import DependencyUpdaterPipeline

class TestDependencyUpdaterPipeline(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.pipeline = DependencyUpdaterPipeline(self.repo_path)

    def test_init_sets_repo_path(self):
        random_path = f"/var/git/{uuid.uuid4().hex}"
        pipeline = DependencyUpdaterPipeline(random_path)
        self.assertEqual(pipeline.repo_path, random_path)

    def test_run_update_pipeline_success(self):
        expected_status = random.choice([True, False])
        mock_scan_result = {uuid.uuid4().hex: uuid.uuid4().hex for _ in range(random.randint(1, 3))}
        
        with patch('skills.dependency_updater_pipeline.DependencyScanner') as MockScanner, \
             patch('skills.dependency_updater_pipeline.VulnerabilityUpdater') as MockUpdater, \
             patch('skills.dependency_updater_pipeline.GitCommitter') as MockCommitter:
            
            scanner_instance = MockScanner.return_value
            scanner_instance.scan.return_value = mock_scan_result
            
            updater_instance = MockUpdater.return_value
            updater_instance.run.return_value = {"updated": expected_status}
            
            committer_instance = MockCommitter.return_value
            committer_instance.commit.return_value = True

            result = self.pipeline.run_update_pipeline()
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), expected_status)
            scanner_instance.scan.assert_called_once()
            updater_instance.run.assert_called_once()

    def test_process_pipeline_stream(self):
        stream_data = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        stream = io.BytesIO(stream_data.encode('utf-8'))
        
        expected_msg = uuid.uuid4().hex

        with patch.object(self.pipeline, 'run_update_pipeline', return_value={"message": expected_msg, "success": True}) as mock_run:
            res = self.pipeline.process_pipeline_stream(stream)
            self.assertTrue(res)
            mock_run.assert_called_once()

    def test_evaluate_and_apply_updates(self):
        dep_name = f"pkg-{uuid.uuid4().hex[:6]}"
        old_version = f"{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,9)}"
        new_version = f"{random.randint(6,9)}.{random.randint(0,9)}.{random.randint(0,9)}"
        
        dependencies_input = {dep_name: {"current": old_version, "latest": new_version}}

        with patch('skills.dependency_updater_pipeline.RepoAutoCommitter') as MockAutoCommitter:
            auto_committer = MockAutoCommitter.return_value
            auto_committer.process_and_commit.return_value = True

            res = self.pipeline.evaluate_and_apply_updates(dependencies_input)
            
            self.assertIsInstance(res, dict)
            self.assertIn(dep_name, res)
            self.assertEqual(res[dep_name].get("applied_version"), new_version)
            auto_committer.process_and_commit.assert_called()

    def test_run_full_cycle(self):
        random_branch = f"feature/{uuid.uuid4().hex[:6]}"
        
        with patch.object(self.pipeline, 'run_update_pipeline', return_value={"status": True}) as mock_update, \
             patch('skills.dependency_updater_pipeline.RepoCIPipeline') as MockCI:
            
            ci_instance = MockCI.return_value
            ci_instance.run_pipeline.return_value = True

            success = self.pipeline.run()
            
            self.assertTrue(success)
            mock_update.assert_called_once()
            ci_instance.run_pipeline.assert_called_once()
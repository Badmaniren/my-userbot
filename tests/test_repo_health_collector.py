import unittest
from unittest.mock import patch
import os
import tempfile
import json
import uuid
import random
import io

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collect_metrics_nonexistent_path(self):
        fake_path = os.path.join(self.repo_path, uuid.uuid4().hex)
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=fake_path)

    def test_collect_metrics_basic_success(self):
        session_id = uuid.uuid4().hex
        threshold = random.randint(1, 100)
        
        result = self.collector.collect_metrics(
            repo_path=self.repo_path,
            session_id=session_id,
            expected_threshold=threshold
        )
        
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["threshold"], threshold)
        self.assertIn("metrics", result)

    def test_collect_metrics_with_log_file(self):
        session_id = uuid.uuid4().hex
        log_filename = f"{uuid.uuid4().hex}_{session_id}_{uuid.uuid4().hex}.log"
        log_filepath = os.path.join(self.repo_path, log_filename)
        
        random_log_content = uuid.uuid4().hex
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(random_log_content)

        result = self.collector.collect_metrics(
            repo_path=self.repo_path,
            session_id=session_id
        )

        self.assertEqual(result["metrics"].get("log_content"), random_log_content)
        
        report_filename = f"report_{session_id}.json"
        report_filepath = os.path.join(self.repo_path, report_filename)
        self.assertTrue(os.path.exists(report_filepath))
        
        with open(report_filepath, "r", encoding="utf-8") as f:
            saved_report = json.load(f)
            self.assertEqual(saved_report["session_id"], session_id)

    def test_collect_metrics_log_read_error(self):
        session_id = uuid.uuid4().hex
        log_filename = f"{session_id}.log"
        log_filepath = os.path.join(self.repo_path, log_filename)
        
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(
                    repo_path=self.repo_path,
                    session_id=session_id
                )

    def test_collect_metrics_report_write_error(self):
        session_id = uuid.uuid4().hex
        
        original_open = open
        def mock_open(file, *args, **kwargs):
            if str(file).endswith(f"report_{session_id}.json"):
                raise PermissionError(uuid.uuid4().hex)
            return original_open(file, *args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(
                    repo_path=self.repo_path,
                    session_id=session_id
                )

if __name__ == "__main__":
    unittest.main()
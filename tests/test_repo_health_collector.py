import unittest
from unittest.mock import patch
import os
import tempfile
import uuid
import random
import json
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):
    def setUp(self):
        self.collector = RepoHealthCollector()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_collect_metrics_path_not_exists(self):
        fake_path = os.path.join(self.repo_path, uuid.uuid4().hex)
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(fake_path)

    def test_collect_metrics_basic(self):
        result = self.collector.collect_metrics(self.repo_path)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertIsNone(result["session_id"])
        self.assertEqual(result["metrics"], {})

    def test_collect_metrics_with_threshold(self):
        threshold_val = random.randint(10, 100)
        result = self.collector.collect_metrics(self.repo_path, expected_threshold=threshold_val)
        self.assertEqual(result["threshold"], threshold_val)

    def test_collect_metrics_with_session_and_log(self):
        session_id = uuid.uuid4().hex
        log_filename = f"{uuid.uuid4().hex}_{session_id}.log"
        log_filepath = os.path.join(self.repo_path, log_filename)
        log_content = uuid.uuid4().hex

        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(log_content)

        result = self.collector.collect_metrics(self.repo_path, session_id=session_id)
        
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["metrics"].get("log_content"), log_content)

        report_filename = f"report_{session_id}.json"
        report_filepath = os.path.join(self.repo_path, report_filename)
        self.assertTrue(os.path.exists(report_filepath))

        with open(report_filepath, "r", encoding="utf-8") as f:
            loaded_report = json.load(f)
            self.assertEqual(loaded_report["status"], "healthy")
            self.assertEqual(loaded_report["session_id"], session_id)
            self.assertEqual(loaded_report["metrics"]["log_content"], log_content)

    def test_collect_metrics_read_error(self):
        session_id = uuid.uuid4().hex
        log_filename = f"{session_id}.log"
        log_filepath = os.path.join(self.repo_path, log_filename)
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(self.repo_path, session_id=session_id)

    def test_collect_metrics_write_error(self):
        session_id = uuid.uuid4().hex
        log_filename = f"{session_id}.log"
        log_filepath = os.path.join(self.repo_path, log_filename)
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(uuid.uuid4().hex)

        original_open = open
        def mock_open(*args, **kwargs):
            if len(args) > 1 and "w" in args[1]:
                raise PermissionError(uuid.uuid4().hex)
            if "mode" in kwargs and "w" in kwargs["mode"]:
                raise PermissionError(uuid.uuid4().hex)
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(self.repo_path, session_id=session_id)

if __name__ == "__main__":
    unittest.main()
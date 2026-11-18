import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import string
import io

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_session_id = uuid.uuid4().hex
        self.random_threshold = random.randint(10, 100)
        self.random_log_content = "".join(random.choices(string.ascii_letters + string.digits, k=50))
        self.random_filename = f"{uuid.uuid4().hex}_{self.random_session_id}.log"

    def test_collect_metrics_nonexistent_repo(self):
        nonexistent_path = f"/nonexistent/{uuid.uuid4().hex}"
        with patch("os.path.exists", return_value=False):
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(nonexistent_path)
            self.assertIn(nonexistent_path, str(ctx.exception))

    def test_collect_metrics_basic_success(self):
        with patch("os.path.exists", return_value=True):
            result = self.collector.collect_metrics(self.random_repo_path)
            self.assertEqual(result["status"], "healthy")
            self.assertEqual(result["repo_path"], self.random_repo_path)
            self.assertIsNone(result["session_id"])
            self.assertEqual(result["metrics"], {})
            self.assertNotIn("threshold", result)

    def test_collect_metrics_with_threshold(self):
        with patch("os.path.exists", return_value=True):
            result = self.collector.collect_metrics(
                self.random_repo_path, 
                expected_threshold=self.random_threshold
            )
            self.assertEqual(result["threshold"], self.random_threshold)

    def test_collect_metrics_with_session_and_logs(self):
        mock_listdir_files = [self.random_filename, f"{uuid.uuid4().hex}.txt"]
        
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=mock_listdir_files), \
             patch("builtins.open", mock_open(read_data=self.random_log_content)) as mock_file, \
             patch("json.dump") as mock_json_dump:
            
            result = self.collector.collect_metrics(
                self.random_repo_path, 
                session_id=self.random_session_id, 
                expected_threshold=self.random_threshold
            )
            
            self.assertEqual(result["status"], "healthy")
            self.assertEqual(result["repo_path"], self.random_repo_path)
            self.assertEqual(result["session_id"], self.random_session_id)
            self.assertEqual(result["threshold"], self.random_threshold)
            self.assertIn("log_content", result["metrics"])
            self.assertEqual(result["metrics"]["log_content"], self.random_log_content)
            
            expected_report_path = os.path.join(self.random_repo_path, f"report_{self.random_session_id}.json")
            mock_json_dump.assert_called_once()
            args, _ = mock_json_dump.call_args
            self.assertEqual(args[0]["session_id"], self.random_session_id)
            self.assertEqual(args[0]["metrics"]["log_content"], self.random_log_content)

    def test_collect_metrics_read_error(self):
        mock_listdir_files = [self.random_filename]
        
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=mock_listdir_files), \
             patch("builtins.open", side_effect=PermissionError("Access denied")):
            
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(
                    self.random_repo_path, 
                    session_id=self.random_session_id
                )
            self.assertIn("Ошибка при чтении лог-файлов", str(ctx.exception))

    def test_collect_metrics_write_report_error(self):
        mock_listdir_files = []
        
        with patch("os.path.exists", return_value=True), \
             patch("os.listdir", return_value=mock_listdir_files), \
             patch("builtins.open", side_effect=[mock_open().return_value, PermissionError("Disk full")]):
            
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(
                    self.random_repo_path, 
                    session_id=self.random_session_id
                )
            self.assertIn("Ошибка при записи отчета", str(ctx.exception))

if __name__ == "__main__":
    unittest.main()
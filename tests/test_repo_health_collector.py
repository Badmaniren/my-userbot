import os
import json
import unittest
import uuid
import random
import string
from unittest.mock import patch, mock_open
import io

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError


class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()

    def test_collect_metrics_nonexistent_repo_raises_error(self):
        nonexistent_path = f"/nonexistent/path/{uuid.uuid4().hex}"
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=nonexistent_path)

    @patch("os.path.exists")
    def test_collect_metrics_basic_success(self, mock_exists):
        mock_exists.return_value = True
        random_repo = f"/repo/{uuid.uuid4().hex}"
        
        result = self.collector.collect_metrics(repo_path=random_repo)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], random_repo)
        self.assertIsNone(result["session_id"])
        self.assertEqual(result["metrics"], {})

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_collect_metrics_with_session_and_threshold(self, mock_json_dump, mock_file_open, mock_listdir, mock_exists):
        mock_exists.return_value = True
        
        session_id = uuid.uuid4().hex
        random_repo = f"/repo/{uuid.uuid4().hex}"
        threshold_value = random.randint(10, 100)
        log_filename = f"{session_id}_{uuid.uuid4().hex}.log"
        log_content = "".join(random.choices(string.ascii_letters + string.whitespace, k=32))
        
        mock_listdir.return_value = [log_filename, f"{uuid.uuid4().hex}.txt"]
        
        # Настраиваем mock_open для чтения файла лога и записи json отчета
        mock_file_open.return_value.read.return_value = log_content

        result = self.collector.collect_metrics(
            repo_path=random_repo,
            session_id=session_id,
            expected_threshold=threshold_value
        )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], random_repo)
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["threshold"], threshold_value)
        self.assertIn("log_content", result["metrics"])
        self.assertEqual(result["metrics"]["log_content"], log_content)

        mock_file_open.assert_any_call(os.path.join(random_repo, log_filename), "r", encoding="utf-8")
        report_filename = os.path.join(random_repo, f"report_{session_id}.json")
        mock_file_open.assert_any_call(report_filename, "w", encoding="utf-8")
        mock_json_dump.assert_called_once()

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_collect_metrics_read_error_raises_repo_health_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        session_id = uuid.uuid4().hex
        random_repo = f"/repo/{uuid.uuid4().hex}"
        log_filename = f"{session_id}_{uuid.uuid4().hex}.log"
        
        mock_listdir.return_value = [log_filename]
        
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(repo_path=random_repo, session_id=session_id)
            self.assertIn("Ошибка при чтении лог-файлов", str(ctx.exception))

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_collect_metrics_write_error_raises_repo_health_error(self, mock_file_open, mock_listdir, mock_exists):
        mock_exists.return_value = True
        session_id = uuid.uuid4().hex
        random_repo = f"/repo/{uuid.uuid4().hex}"
        log_filename = f"{session_id}_{uuid.uuid4().hex}.log"
        
        mock_listdir.return_value = [log_filename]
        mock_file_open.return_value.read.return_value = uuid.uuid4().hex

        with patch("json.dump", side_effect=IOError("Disk full")):
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(repo_path=random_repo, session_id=session_id)
            self.assertIn("Ошибка при записи отчета", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
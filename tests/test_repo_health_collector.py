import os
import json
import unittest
import uuid
import random
import io
from unittest.mock import patch, mock_open
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_session_id = uuid.uuid4().hex
        self.random_threshold = random.randint(100, 9999)
        self.random_log_content = uuid.uuid4().hex

    def test_collect_metrics_repo_not_exists(self):
        non_existent_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=non_existent_path)

    @patch("os.path.exists")
    def test_collect_metrics_success_without_session(self, mock_exists):
        mock_exists.return_value = True
        
        result = self.collector.collect_metrics(repo_path=self.random_repo_path)
        
        self.assertEqual(result["status"], "healthy")
        self.assertIsNone(result["session_id"])
        self.assertEqual(result["repo_path"], self.random_repo_path)
        self.assertEqual(result["metrics"], {})
        self.assertNotIn("threshold", result)

    @patch("os.path.exists")
    def test_collect_metrics_success_with_threshold(self, mock_exists):
        mock_exists.return_value = True
        
        result = self.collector.collect_metrics(
            repo_path=self.random_repo_path, 
            expected_threshold=self.random_threshold
        )
        
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["threshold"], self.random_threshold)

    @patch("os.path.exists")
    @patch("os.listdir")
    @patch("builtins.open", new_callable=mock_open)
    def test_collect_metrics_with_session_success(self, mock_file_open, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{self.random_session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_filename, f"{uuid.uuid4().hex}.txt"]
        
        mock_file_open.return_value.read.return_value = self.random_log_content

        result = self.collector.collect_metrics(
            repo_path=self.random_repo_path,
            session_id=self.random_session_id,
            expected_threshold=self.random_threshold
        )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["session_id"], self.random_session_id)
        self.assertEqual(result["metrics"]["log_content"], self.random_log_content)
        self.assertEqual(result["threshold"], self.random_threshold)
        
        mock_file_open.assert_any_call(os.path.join(self.random_repo_path, log_filename), "r", encoding="utf-8")
        report_filename = f"report_{self.random_session_id}.json"
        mock_file_open.assert_any_call(os.path.join(self.random_repo_path, report_filename), "w", encoding="utf-8")

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_collect_metrics_read_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{self.random_session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_filename]

        file_path = os.path.join(self.random_repo_path, log_filename)
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)) as mock_file:
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(
                    repo_path=self.random_repo_path,
                    session_id=self.random_session_id
                )

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_collect_metrics_write_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{self.random_session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_filename]

        def side_effect_open(*args, **kwargs):
            if "w" in args[1]:
                raise Exception(uuid.uuid4().hex)
            return mock_open(read_data=self.random_log_content).return_value

        with patch("builtins.open", side_effect=side_effect_open):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(
                    repo_path=self.random_repo_path,
                    session_id=self.random_session_id
                )

    def test_io_bytes_stream_integration(self):
        stream = io.BytesIO(uuid.uuid4().bytes)
        self.assertIsNotNone(stream.read())

if __name__ == "__main__":
    unittest.main()
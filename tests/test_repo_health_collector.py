import unittest
from unittest.mock import patch, mock_open
import os
import json
import uuid
import random
import io

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()
        self.valid_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.session_id = uuid.uuid4().hex
        self.threshold = random.randint(1, 100)
        self.random_log_content = uuid.uuid4().hex

    def test_collect_metrics_repo_not_exists(self):
        non_existent_path = f"/non_existent_{uuid.uuid4().hex}"
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(non_existent_path)

    @patch("os.path.exists")
    def test_collect_metrics_success_without_session(self, mock_exists):
        mock_exists.return_value = True
        
        result = self.collector.collect_metrics(self.valid_repo_path, expected_threshold=self.threshold)
        
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.valid_repo_path)
        self.assertIsNone(result["session_id"])
        self.assertEqual(result["threshold"], self.threshold)
        self.assertEqual(result["metrics"], {})

    @patch("json.dump")
    @patch("os.path.exists")
    @patch("os.listdir")
    def test_collect_metrics_with_session_and_logs(self, mock_listdir, mock_exists, mock_json_dump):
        mock_exists.return_value = True
        log_filename = f"{self.session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_filename, f"other_{uuid.uuid4().hex}.log"]

        m_open = mock_open(read_data=self.random_log_content)
        
        with patch("builtins.open", m_open):
            result = self.collector.collect_metrics(
                self.valid_repo_path, 
                session_id=self.session_id, 
                expected_threshold=self.threshold
            )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["session_id"], self.session_id)
        self.assertEqual(result["metrics"]["log_content"], self.random_log_content)
        self.assertEqual(result["threshold"], self.threshold)

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_collect_metrics_read_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{self.session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_filename]

        m_open = mock_open()
        m_open.side_effect = IOError(uuid.uuid4().hex)

        with patch("builtins.open", m_open):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(self.valid_repo_path, session_id=self.session_id)

    @patch("os.path.exists")
    @patch("os.listdir")
    def test_collect_metrics_write_report_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{self.session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_filename]

        def side_effect_open(*args, **kwargs):
            if "report" in str(args[0]):
                raise IOError(uuid.uuid4().hex)
            return mock_open(read_data=self.random_log_content).return_value

        with patch("builtins.open", side_effect=side_effect_open):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(self.valid_repo_path, session_id=self.session_id)

if __name__ == "__main__":
    unittest.main()
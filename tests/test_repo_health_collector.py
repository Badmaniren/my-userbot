import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import io
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()
        self.random_repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.random_session_id = uuid.uuid4().hex
        self.random_threshold = random.randint(1, 100)
        self.random_log_content = uuid.uuid4().hex

    def test_collect_metrics_nonexistent_repo(self):
        non_existent_path = f"/nonexistent/{uuid.uuid4().hex}"
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(non_existent_path)

    @patch("skills.repo_health_collector.os.path.exists")
    def test_collect_metrics_basic_success(self, mock_exists):
        mock_exists.return_value = True
        result = self.collector.collect_metrics(self.random_repo_path)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.random_repo_path)
        self.assertIsNone(result["session_id"])
        self.assertEqual(result["metrics"], {})
        self.assertNotIn("threshold", result)

    @patch("skills.repo_health_collector.os.path.exists")
    def test_collect_metrics_with_threshold(self, mock_exists):
        mock_exists.return_value = True
        result = self.collector.collect_metrics(
            repo_path=self.random_repo_path,
            expected_threshold=self.random_threshold
        )
        
        self.assertEqual(result["threshold"], self.random_threshold)

    @patch("skills.repo_health_collector.os.path.exists")
    @patch("skills.repo_health_collector.os.listdir")
    def test_collect_metrics_with_session_success(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{uuid.uuid4().hex}_{self.random_session_id}_data.log"
        mock_listdir.return_value = [log_filename, f"{uuid.uuid4().hex}.txt"]

        mock_file_data = io.StringIO(self.random_log_content)

        with patch("skills.repo_health_collector.open", mock_open(read_data=self.random_log_content)) as m_open:
            result = self.collector.collect_metrics(
                repo_path=self.random_repo_path,
                session_id=self.random_session_id
            )

        self.assertEqual(result["session_id"], self.random_session_id)
        self.assertEqual(result["metrics"]["log_content"], self.random_log_content)
        m_open.assert_any_call(os.path.join(self.random_repo_path, log_filename), "r", encoding="utf-8")
        report_filename = os.path.join(self.random_repo_path, f"report_{self.random_session_id}.json")
        m_open.assert_any_call(report_filename, "w", encoding="utf-8")

    @patch("skills.repo_health_collector.os.path.exists")
    @patch("skills.repo_health_collector.os.listdir")
    def test_collect_metrics_read_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{uuid.uuid4().hex}_{self.random_session_id}.log"
        mock_listdir.return_value = [log_filename]

        with patch("skills.repo_health_collector.open", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(
                    repo_path=self.random_repo_path,
                    session_id=self.random_session_id
                )

    @patch("skills.repo_health_collector.os.path.exists")
    @patch("skills.repo_health_collector.os.listdir")
    def test_collect_metrics_write_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        log_filename = f"{uuid.uuid4().hex}_{self.random_session_id}.log"
        mock_listdir.return_value = [log_filename]

        def side_effect_open(path, mode="r", encoding=None):
            if "report" in path:
                raise Exception(uuid.uuid4().hex)
            return mock_open(read_data=self.random_log_content).return_value

        with patch("skills.repo_health_collector.open", side_effect=side_effect_open):
            with self.assertRaises(RepoHealthError):
                self.collector.collect_metrics(
                    repo_path=self.random_repo_path,
                    session_id=self.random_session_id
                )

if __name__ == "__main__":
    unittest.main()
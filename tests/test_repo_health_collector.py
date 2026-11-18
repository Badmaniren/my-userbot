import unittest
from unittest.mock import patch, mock_open
import os
import uuid
import random
import io
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollectorStrict(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = f"/tmp/{uuid.uuid4().hex}"
        self.collector = RepoHealthCollector(self.repo_path_val)

    def test_init_with_repo_path(self):
        rnd_path = f"/var/repo/{uuid.uuid4().hex}"
        collector = RepoHealthCollector(rnd_path)
        self.assertIsNotNone(collector.logger)

    def test_init_without_repo_path(self):
        collector = RepoHealthCollector()
        self.assertIsNone(collector.logger)

    @patch('os.path.exists')
    def test_collect_metrics_invalid_path_raises_error(self, mock_exists):
        mock_exists.return_value = False
        bad_path = f"/invalid/path/{uuid.uuid4().hex}"
        collector = RepoHealthCollector()
        
        with self.assertRaises(RepoHealthError) as ctx:
            collector.collect_metrics(bad_path)
        
        self.assertIn(bad_path, str(ctx.exception))

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_collect_metrics_with_session_success(self, mock_file_open, mock_listdir, mock_exists):
        mock_exists.return_value = True
        session_id = uuid.uuid4().hex
        log_file_name = f"session_{session_id}_{uuid.uuid4().hex}.log"
        mock_listdir.return_value = [log_file_name, f"{uuid.uuid4().hex}.txt"]
        
        random_content = uuid.uuid4().hex
        mock_file_open.return_value.read.return_value = random_content

        threshold = random.randint(10, 100)
        
        result = self.collector.collect_metrics(
            repo_path=self.repo_path_val,
            session_id=session_id,
            expected_threshold=threshold
        )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.repo_path_val)
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["threshold"], threshold)
        self.assertEqual(result["metrics"]["log_content"], random_content)

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_collect_metrics_read_error(self, mock_listdir, mock_exists):
        mock_exists.return_value = True
        session_id = uuid.uuid4().hex
        mock_listdir.return_value = [f"session_{session_id}.log"]

        with patch('builtins.open', side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(self.repo_path_val, session_id=session_id)
            self.assertIn("Ошибка при чтении лог-файлов", str(ctx.exception))

    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=mock_open)
    def test_collect_metrics_write_report_error(self, mock_file_open, mock_listdir, mock_exists):
        mock_exists.return_value = True
        session_id = uuid.uuid4().hex
        mock_listdir.return_value = []

        def side_effect_open(*args, **kwargs):
            filename = args[0]
            if f"report_{session_id}.json" in filename:
                raise OSError(uuid.uuid4().hex)
            return mock_open()().return_value

        with patch('builtins.open', side_effect=side_effect_open):
            with self.assertRaises(RepoHealthError) as ctx:
                self.collector.collect_metrics(self.repo_path_val, session_id=session_id)
            self.assertIn("Ошибка при записи отчета", str(ctx.exception))

    @patch('os.path.exists')
    def test_collect_metrics_without_session(self, mock_exists):
        mock_exists.return_value = True
        threshold = random.randint(1, 50)
        
        result = self.collector.collect_metrics(
            repo_path=self.repo_path_val,
            expected_threshold=threshold
        )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.repo_path_val)
        self.assertIsNone(result["session_id"])
        self.assertEqual(result["threshold"], threshold)
        self.assertEqual(result["metrics"], {})
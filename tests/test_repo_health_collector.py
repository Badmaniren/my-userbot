import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollector(unittest.TestCase):

    def setUp(self):
        self.collector = RepoHealthCollector()
        self.random_repo_name = f"repo_{uuid.uuid4().hex[:8]}"
        self.random_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        self.random_metric_value = random.randint(10, 1000)
        self.random_error_msg = f"err_{uuid.uuid4().hex[:10]}"

    def test_collect_metrics_success(self):
        expected_data = {
            self.random_metric_key: self.random_metric_value,
            "status": "healthy"
        }
        json_bytes = json.dumps(expected_data).encode('utf-8')
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content = lambda chunk_size: [json_bytes]

        with
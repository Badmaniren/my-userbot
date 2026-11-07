import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.repo_performance_profiler import start_new

class TestRepoPerformanceProfiler(unittest.TestCase):

    def setUp(self):
        self.random_epic_name = f"epic_{uuid.uuid4().hex[:8]}"
        self.random_metric_id = str(uuid.uuid4())
        self.random_threshold = random.randint(100, 9999)
        self.random_path = f"/var/repo/{uuid.uuid4().hex[:6]}/metrics"
        self.random_url = f"https://api.gitrepo.internal/{uuid.uuid4().hex[:10]}/profile"

    def test_start_new_success_flow(self):
        mock_response_data = {
            "status": "initialized",
            "epic": self.random_epic_name,
            "metric_id": self.random_metric_id,
            "threshold": self.random_threshold
        }

        with patch("skills.repo_performance_profiler.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 201
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            result = start_new(
                epic_name=self.random_epic_name,
                target_path=self.random_path,
                endpoint_url=self.random_url,
                threshold=self.random_threshold
            )

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            self.assertEqual(call_args[0][0], self.random_url)
            self.assertIn(self.random_epic_name, str(call_args[1]))
            self.assertEqual(result["epic"], self.random_epic_name)
            self.assertEqual(result["metric_id"], self.random_metric_id)

    def test_start_new_invalid_response_stream(self):
        random_garbage = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        mock_stream = io.BytesIO(random_garbage)

        with patch("skills.repo_performance_profiler.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.raw = mock_stream
            mock_resp.text = random_garbage.decode('utf-8')
            mock_post.return_value = mock_resp

            with self.assertRaises(Exception) as context:
                start_new(
                    epic_name=self.random_epic_name,
                    target_path=self.random_path,
                    endpoint_url=self.random_url,
                    threshold=self.random_threshold
                )
            
            self.assertTrue(len(str(context.exception)) > 0)

    def test_start_new_file_metric_generation(self):
        mock_file_content = f"METRIC_KEY={self.random_metric_id}\nLIMIT={self.random_threshold}".encode('utf-8')
        mock_file = io.BytesIO(mock_file_content)

        with patch("skills.repo_performance_profiler.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = mock_file

            with patch("skills.repo_performance_profiler.os.path.exists", return_value=True):
                result = start_new(
                    epic_name=self.random_epic_name,
                    target_path=self.random_path,
                    endpoint_url=self.random_url,
                    threshold=self.random_threshold
                )

                self.assertIsInstance(result, dict)
                self.assertIn("metric_id", result)

if __name__ == "__main__":
    unittest.main()
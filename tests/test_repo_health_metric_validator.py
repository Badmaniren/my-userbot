import unittest
import json
import io
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics
)

class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()

    def _generate_random_metric(self):
        return {
            "metric_name": uuid.uuid4().hex,
            "score": random.uniform(0.0, 100.0),
            "timestamp": uuid.uuid4().hex
        }

    def test_validate_success(self):
        metric = self._generate_random_metric()
        self.assertTrue(self.validator.validate(metric))

    def test_validate_invalid_types(self):
        with self.assertRaises(MetricValidationError):
            self.validator.validate(uuid.uuid4().hex)

    def test_validate_missing_fields(self):
        metric = self._generate_random_metric()
        del metric[random.choice(["metric_name", "score", "timestamp"])]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_score_bounds(self):
        metric = self._generate_random_metric()
        metric["score"] = random.uniform(101.0, 200.0)
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_stream_json_array(self):
        metrics = [self._generate_random_metric() for _ in range(3)]
        stream = io.BytesIO(json.dumps(metrics).encode('utf-8'))
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["metric_name"], metrics[0]["metric_name"])

    def test_validate_stream_invalid_json(self):
        stream = io.BytesIO(b"invalid_json_data_" + uuid.uuid4().hex.encode())
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_dispatch_and_validate_remote(self):
        metric = self._generate_random_metric()
        endpoint = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "accepted", "id": uuid.uuid4().hex}
        
        with patch('requests.post') as mock_post:
            mock_post.return_value = mock_response
            result = self.validator.dispatch_and_validate_remote(metric, endpoint)
            
            mock_post.assert_called_once()
            self.assertEqual(result["status"], "accepted")

    def test_audit_repository(self):
        metric = self._generate_random_metric()
        result = audit_repository(metric)
        self.assertEqual(result["metric_name"], metric["metric_name"])

    def test_render_health_dashboard(self):
        name = uuid.uuid4().hex
        score = random.uniform(0, 100)
        metric = {"metric_name": name, "score": score}
        output = render_health_dashboard(metric)
        self.assertIn(name, output)
        self.assertIn(str(score), output)

    def test_validate_repo_health_metrics_transformation(self):
        run_id = uuid.uuid4().hex
        health_score = random.uniform(0, 100)
        payload = {"run_id": run_id, "health_score": health_score, "timestamp": uuid.uuid4().hex}
        
        result = validate_repo_health_metrics(payload)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], health_score)

    def test_validate_repo_health_metrics_failure(self):
        payload = {"invalid": uuid.uuid4().hex}
        result = validate_repo_health_metrics(payload)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"], payload)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import json

from skills.repo_health_metric_validator import RepoHealthMetricValidator, MetricValidationError

class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10)) + "_" + uuid.uuid4().hex[:6]
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1600000000, 1900000000)

    def test_validate_metric_success(self):
        valid_metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "status": "HEALTHY"
        }
        
        result = self.validator.validate(valid_metric_data)
        self.assertTrue(result)

    def test_validate_metric_missing_mandatory_field(self):
        invalid_metric_data = {
            "metric_name": self.random_metric_name,
            "timestamp": self.random_timestamp
        }
        
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_metric_data)
        
        self.assertIn("score", str(ctx.exception))

    def test_validate_metric_out_of_bounds_score(self):
        bad_score = 105.5 + random.uniform(1.0, 50.0)
        invalid_metric_data = {
            "metric_name": self.random_metric_name,
            "score": bad_score,
            "timestamp": self.random_timestamp,
            "status": "CRITICAL"
        }
        
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_metric_data)
        
        self.assertIn("score", str(ctx.exception))

    def test_validate_batch_metrics_from_stream(self):
        metric_id_1 = uuid.uuid4().hex
        metric_id_2 = uuid.uuid4().hex
        
        raw_stream_data = json.dumps([
            {"metric_name": metric_id_1, "score": 85.5, "timestamp": self.random_timestamp},
            {"metric_name": metric_id_2, "score": 42.1, "timestamp": self.random_timestamp + 10}
        ]).encode('utf-8')
        
        mock_stream = io.BytesIO(raw_stream_data)
        
        with patch('skills.repo_health_metric_validator.open', create=True) as mock_open:
            mock_open.return_value = mock_stream
            
            validated_metrics = self.validator.validate_stream(mock_stream)
            
            self.assertEqual(len(validated_metrics), 2)
            self.assertEqual(validated_metrics[0]["metric_name"], metric_id_1)
            self.assertEqual(validated_metrics[1]["metric_name"], metric_id_2)

    def test_validate_stream_malformed_payload(self):
        garbage_bytes = uuid.uuid4().bytes + b"\xff\x00\xaa" + string.ascii_letters.encode('utf-8')
        mock_stream = io.BytesIO(garbage_bytes)
        
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(mock_stream)

    def test_external_gateway_validation_hook(self):
        endpoint_token = uuid.uuid4().hex
        mock_response_payload = {
            "status": "ACCEPTED",
            "validation_token": endpoint_token
        }
        
        with patch('requests.post') as mock_post:
            instance_mock = MagicMock()
            instance_mock.status_code = 200
            instance_mock.json.return_value = mock_response_payload
            mock_post.return_value = instance_mock
            
            payload = {
                "metric_name": self.random_metric_name,
                "score": self.random_score,
                "timestamp": self.random_timestamp
            }
            
            response = self.validator.dispatch_and_validate_remote(payload, f"http://localhost/{uuid.uuid4().hex}")
            
            self.assertEqual(response["validation_token"], endpoint_token)
            mock_post.assert_called_once()
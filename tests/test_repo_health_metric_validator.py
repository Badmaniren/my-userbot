import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string

from skills.repo_health_metric_validator import (
    MetricValidationError,
    RepoHealthMetricValidator,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics,
)


class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()

    def test_validate_success(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1500000000, 1800000000)
        
        payload = {
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp
        }

        result = self.validator.validate(payload)
        self.assertTrue(result)

    def test_validate_not_a_dictionary_raises_error(self):
        invalid_input = random.choice([
            random.randint(1, 1000),
            f"string_{uuid.uuid4().hex}",
            ["list_item", uuid.uuid4().hex]
        ])
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_input)

    def test_validate_missing_mandatory_fields_raises_error(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1500000000, 1800000000)

        missing_name = {"score": score, "timestamp": timestamp}
        missing_score = {"metric_name": metric_name, "timestamp": timestamp}
        missing_timestamp = {"metric_name": metric_name, "score": score}

        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_name)

        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_score)

        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_timestamp)

    def test_validate_invalid_score_types_raises_error(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        timestamp = random.randint(1500000000, 1800000000)
        
        invalid_scores = [
            True,
            False,
            f"score_{uuid.uuid4().hex[:4]}",
            None,
            [random.randint(1, 100)]
        ]

        for bad_score in invalid_scores:
            payload = {
                "metric_name": metric_name,
                "score": bad_score,
                "timestamp": timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(payload)

    def test_validate_score_out_of_bounds_raises_error(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        timestamp = random.randint(1500000000, 1800000000)
        
        out_of_bounds = [
            round(random.uniform(-1000.0, -0.01), 2),
            round(random.uniform(100.01, 1000.0), 2)
        ]

        for bad_score in out_of_bounds:
            payload = {
                "metric_name": metric_name,
                "score": bad_score,
                "timestamp": timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(payload)

    def test_validate_stream_with_string_and_bytes(self):
        metric_name = f"stream_metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1500000000, 1800000000)
        
        metric_dict = {
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp
        }

        json_data = json.dumps(metric_dict)

        result_str = self.validator.validate_stream(json_data)
        self.assertEqual(len(result_str), 1)
        self.assertEqual(result_str[0]["metric_name"], metric_name)
        self.assertEqual(result_str[0]["score"], score)

        bytes_data = json_data.encode('utf-8')
        result_bytes = self.validator.validate_stream(bytes_data)
        self.assertEqual(len(result_bytes), 1)
        self.assertEqual(result_bytes[0]["metric_name"], metric_name)

    def test_validate_stream_with_io_object(self):
        metric_name = f"io_metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1500000000, 1800000000)
        
        payload = [{
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp
        }]

        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], metric_name)

    def test_validate_stream_invalid_bytes_decoding(self):
        invalid_bytes = b'\xff\xfe\xfd_invalid_utf8'
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(invalid_bytes)

    def test_validate_stream_invalid_json(self):
        bad_json = f"{{malformed_json_{uuid.uuid4().hex}}}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_json)

    def test_dispatch_and_validate_remote(self):
        metric_name = f"remote_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1500000000, 1800000000)
        
        payload = {
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp
        }
        
        endpoint_url = f"https://{uuid.uuid4().hex[:10]}.example.com/api/{uuid.uuid4().hex[:6]}"
        expected_response_data = {"status": "success", "received_metric": metric_name}

        with patch("skills.repo_health_metric_validator.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response_data
            mock_post.return_value = mock_response

            response = self.validator.dispatch_and_validate_remote(payload, endpoint_url)
            
            mock_post.assert_called_once_with(endpoint_url, json=payload)
            self.assertEqual(response, expected_response_data)

    def test_audit_repository(self):
        metric_name = f"audit_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1500000000, 1800000000)
        
        data = {
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp
        }

        result = audit_repository(data)
        self.assertEqual(result, data)

    def test_render_health_dashboard(self):
        metric_name = f"dash_{uuid.uuid4().hex[:8]}"
        data = {"metric_name": metric_name}
        res = render_health_dashboard(data)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_normalization_and_validation(self):
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        health_score = round(random.uniform(0.0, 100.0), 2)
        
        input_data = {
            "run_id": run_id,
            "health_score": health_score
        }

        output = validate_repo_health_metrics(input_data)
        self.assertTrue(output["is_valid"])
        self.assertEqual(output["metrics"]["metric_name"], run_id)
        self.assertEqual(output["metrics"]["score"], health_score)
        self.assertIn("timestamp", output["metrics"])

    def test_validate_repo_health_metrics_invalid(self):
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        invalid_score = round(random.uniform(105.0, 500.0), 2)
        
        input_data = {
            "run_id": run_id,
            "health_score": invalid_score
        }

        output = validate_repo_health_metrics(input_data)
        self.assertFalse(output["is_valid"])
        self.assertEqual(output["metrics"]["score"], invalid_score)
import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
from skills.repo_health_metric_validator import (
    MetricValidationError,
    RepoHealthMetricValidator,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics
)


class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_validate_success(self):
        valid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        self.assertTrue(self.validator.validate(valid_data))

    def test_validate_not_dict_raises(self):
        invalid_data = [self.random_metric_name, self.random_score]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_metric_name_raises(self):
        invalid_data = {
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_score_raises(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_timestamp_raises(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_invalid_score_type_raises(self):
        for bad_score in [f"str_{uuid.uuid4().hex[:4]}", True, False, None, {}]:
            invalid_data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds_raises(self):
        for bad_score in [-random.uniform(0.1, 1000.0), 100.0 + random.uniform(0.1, 1000.0)]:
            invalid_data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_stream_bytes_success
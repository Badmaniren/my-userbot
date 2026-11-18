import unittest
from unittest.mock import patch
import io
import json
import uuid
import random

from skills.repo_health_analytics_transformer import (
    RepoHealthAnalyticsэффициентTransformer,
    RepoHealthTransformationError,
    transform_health_metrics,
    repo_health_analytics_transformer
)

class TestRepoHealthAnalyticsTransformer(unittest.TestCase):
    def setUp(self):
        self.transformer = RepoHealthAnalyticsэффициентTransformer()
        self.rand_repo_id = uuid.uuid4().hex
        self.rand_metric_key = uuid.uuid4().hex
        self.rand_score = random.randint(1, 100)
        self.rand_status = random.choice(["OK", "WARN", "CRITICAL"])

    def test_transform_valid_raw_data(self):
        payload = {
            "repository_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_key: {
                    "score": self.rand_score,
                    "status": self.rand_status
                }
            }
        }
        result = self.transformer.transform(payload)
        self.assertEqual(result["repo_uuid"], self.rand_repo_id)
        self.assertIn(self.rand_metric_key, result["normalized_metrics"])
        self.assertEqual(result["normalized_metrics"][self.rand_metric_key]["value"], self.rand_score)
        self.assertEqual(result["normalized_metrics"][self.rand_metric_key]["severity"], self.rand_status)

    def test_transform_already_normalized_data(self):
        payload = {
            "repo_uuid": self.rand_repo_id,
            "normalized_score": random.uniform(0.0, 1.0)
        }
        result = self.transformer.transform(payload)
        self.assertEqual(result, payload)

    def test_transform_invalid_data_raises_error(self):
        invalid_payloads = [
            uuid.uuid4().hex,
            {uuid.uuid4().hex: random.randint(1, 10)},
            None
        ]
        for p in invalid_payloads:
            with self.assertRaises(RepoHealthTransformationError):
                self.transformer.transform(p)

    def test_transform_stream(self):
        payload = {
            "repository_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_key: {
                    "score": self.rand_score,
                    "status": self.rand_status
                }
            }
        }
        stream = io.BytesIO(json.dumps(payload).encode("utf-8"))
        result = self.transformer.transform_stream(stream)
        self.assertEqual(result["repo_uuid"], self.rand_repo_id)
        self.assertEqual(result["normalized_metrics"][self.rand_metric_key]["value"], self.rand_score)

    def test_transform_health_metrics_wrapper(self):
        payload = {
            "repository_id": self.rand_repo_id,
            "metrics": {
                self.rand_metric_key: {
                    "score": self.rand_score,
                    "status": self.rand_status
                }
            }
        }
        result = transform_health_metrics(payload)
        self.assertEqual(result["repo_uuid"], self.rand_repo_id)

    def test_repo_health_analytics_transformer_integration_valid(self):
        health_score = random.randint(10, 99)
        open_issues = random.randint(0, 50)
        validated_data = {
            "repository_id": self.rand_repo_id,
            "health_score": health_score,
            "open_issues": open_issues
        }
        result = repo_health_analytics_transformer(validated_data)
        self.assertEqual(result["repository_id"], self.rand_repo_id)
        self.assertEqual(result["normalized_score"], health_score)
        self.assertEqual(result["metrics_summary"]["open_issues"], open_issues)
        self.assertTrue(result["transformed_at"])

    def test_repo_health_analytics_transformer_integration_invalid(self):
        with self.assertRaises(RepoHealthTransformationError):
            repo_health_analytics_transformer(uuid.uuid4().hex)

    def test_transform_with_repo_uuid_key(self):
        payload = {
            "repo_uuid": self.rand_repo_id,
            "metrics": {}
        }
        result = self.transformer.transform(payload)
        self.assertEqual(result["repo_uuid"], self.rand_repo_id)
import unittest
import json
import uuid
import random
import io
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    validate_repo_health_metrics,
    audit_repository
)

class TestRepoHealthMetricValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = RepoHealthMetricValidator()

    def generate_random_metric(self):
        return {
            "metric_name": f"metric_{uuid.uuid4().hex[:8]}",
            "score": round(random.uniform(0.0, 100.0), 2),
            "timestamp": random.randint(1600000000, 1700000000)
        }

    def test_full_stream_processing_integration(self):
        # Генерируем набор случайных метрик
        count = random.randint(3, 7)
        metrics = [self.generate_random_metric() for _ in range(count)]
        stream_data = json.dumps(metrics)
        stream = io.StringIO(stream_data)

        # Проверка потоковой обработки
        validated = self.validator.validate_stream(stream)
        self.assertEqual(len(validated), count)
        self.assertEqual(validated[0]["metric_name"], metrics[0]["metric_name"])

    def test_normalization_and_validation_flow(self):
        # Тест интеграции нормализатора с валидатором
        raw_payload = {
            "run_id": f"test_run_{uuid.uuid4().hex[:4]}",
            "health_score": random.uniform(10.0, 90.0),
            "timestamp": random.randint(1600000000, 1700000000)
        }
        
        result = validate_repo_health_metrics(raw_payload)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], raw_payload["run_id"])
        self.assertEqual(result["metrics"]["score"], raw_payload["health_score"])

    def test_audit_repository_integrity(self):
        # Проверка сквозного аудита
        metric = self.generate_random_metric()
        audited = audit_repository(metric)
        
        self.assertEqual(audited["metric_name"], metric["metric_name"])
        self.assertEqual(audited["score"], metric["score"])

    def test_invalid_data_rejection(self):
        # Проверка обработки некорректных данных
        bad_metric = {
            "metric_name": "bad_metric",
            "score": 150.0, # Выход за границы
            "timestamp": 123456789
        }
        
        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_metric)

    def test_stream_bytes_decoding(self):
        # Проверка обработки байтового потока
        metric = self.generate_random_metric()
        byte_stream = io.BytesIO(json.dumps(metric).encode('utf-8'))
        
        validated = self.validator.validate_stream(byte_stream)
        self.assertEqual(validated[0]["metric_name"], metric["metric_name"])

if __name__ == "__main__":
    unittest.main()
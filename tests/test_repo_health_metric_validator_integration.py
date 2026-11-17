import unittest
import uuid
import random
import json
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    validate_repo_health_metrics,
    audit_repository,
    render_health_dashboard
)

class TestRepoHealthMetricValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.test_id = str(uuid.uuid4())
        self.test_score = round(random.uniform(0.0, 100.0), 2)
        self.test_timestamp = "2023-10-27T10:00:00Z"

    def test_full_integration_flow(self):
        # 1. Генерация данных с использованием случайных значений
        raw_payload = {
            "run_id": f"metric_{self.test_id}",
            "health_score": self.test_score,
            "timestamp": self.test_timestamp
        }

        # 2. Проверка нормализации через validate_repo_health_metrics
        normalized_result = validate_repo_health_metrics(raw_payload)
        self.assertTrue(normalized_result["is_valid"])
        self.assertEqual(normalized_result["metrics"]["metric_name"], f"metric_{self.test_id}")
        self.assertEqual(normalized_result["metrics"]["score"], self.test_score)

        # 3. Проверка аудита (сквозная передача)
        audited_data = audit_repository(normalized_result["metrics"])
        self.assertEqual(audited_data["metric_name"], f"metric_{self.test_id}")

        # 4. Проверка рендеринга дашборда
        dashboard_output = render_health_dashboard(audited_data)
        self.assertIn(f"Metric: metric_{self.test_id}", dashboard_output)
        self.assertIn(f"Score: {self.test_score}", dashboard_output)

    def test_stream_processing_integration(self):
        # Генерация списка случайных метрик для потоковой обработки
        stream_data = [
            {
                "metric_name": f"test_metric_{uuid.uuid4()}",
                "score": random.uniform(0, 100),
                "timestamp": self.test_timestamp
            } for _ in range(3)
        ]
        
        json_stream = json.dumps(stream_data)
        
        # Валидация потока через основной класс
        validated_list = self.validator.validate_stream(json_stream)
        
        self.assertEqual(len(validated_list), 3)
        self.assertEqual(validated_list[0]["metric_name"], stream_data[0]["metric_name"])

    def test_invalid_data_handling(self):
        # Проверка на выброс исключения при некорректных данных
        bad_payload = {
            "metric_name": "broken_metric",
            "score": 150.0,  # Выход за границы
            "timestamp": self.test_timestamp
        }
        
        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        # Проверка, что функция нормализации корректно возвращает is_valid=False
        result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(result["is_valid"])

if __name__ == "__main__":
    unittest.main()
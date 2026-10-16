import unittest
import os
import tempfile
import uuid
import random
from skills.anomaly_visualizer import AnomalyVisualizer, start_new
from skills.git_inspector import GitInspector


class TestAnomalyVisualizerIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        # Инициализируем реальный GitInspector без моков, как требует интеграционный тест
        self.git_inspector = GitInspector(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_statistical_report_integration_with_git_and_random_data(self):
        # Генерируем случайные данные для исключения хардкода
        unique_run_id = f"run-{uuid.uuid4()}"
        random_score = round(random.uniform(0.0, 1.0), 4)
        filename = f"report_{uuid.uuid4()}.html"
        
        data_points_count = random.randint(5, 50)
        random_data = [random.randint(100, 999) for _ in range(data_points_count)]
        
        metadata = {
            "run_id": unique_run_id,
            "score": random_score,
            "repo_path": self.repo_path
        }

        # Создаем экземпляр тестируемого модуля AnomalyVisualizer
        visualizer = AnomalyVisualizer(
            git_inspector=self.git_inspector,
            output_dir=self.repo_path
        )

        # Вызываем реальный метод генерации отчета
        report_path = visualizer.generate_statistical_report(
            data=random_data,
            filename=filename,
            metadata=metadata
        )

        # Проверяем, что файл действительно создан на диске
        self.assertTrue(os.path.exists(report_path), "Интеграционный отчет не был создан в файловой системе")

        # Читаем содержимое созданного файла и проверяем наличие уникальных сгенерированных данных
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(unique_run_id, content, "Уникальный run_id отсутствует в сгенерированном отчете")
        self.assertIn(str(random_score), content, "Случайный score отсутствует в сгенерированном отчете")
        self.assertIn(f"Data points: {data_points_count}", content, "Количество точек данных не совпадает с переданным")

    def test_start_new_handler_with_stream_and_random_token(self):
        random_token = str(uuid.uuid4())
        random_payload = f"anomaly_payload_{uuid.uuid4()}".encode("utf-8")
        
        stream = io.BytesIO(random_payload)
        
        result = start_new(stream, token=random_token)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("processed_bytes"), len(random_payload))
        self.assertEqual(result.get("token"), random_token)


if __name__ == "__main__":
    unittest.main()
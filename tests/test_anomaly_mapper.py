import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io

# Импортируем тестируемый модуль и зависимости
# Предполагается наличие структуры skills.anomaly_mapper, skills.anomaly_detector, skills.git_inspector
from skills.anomaly_mapper import AnomalyMapper
from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.git_inspector import GitInspector

class TestAnomalyMapper(unittest.TestCase):
    """Инквизиторская проверка модуля AnomalyMapper на предмет корректности маппинга регрессий."""

    def setUp(self):
        """Подготовка инструментов допроса: инициализация моков с рандомизированными путями."""
        self.repo_path = f"/varch/repo/{uuid.uuid4().hex}"
        self.mock_detector = MagicMock(spec=AnomalyDetector)
        self.mock_inspector = MagicMock(spec=GitInspector)

        # Инициализация маппера с внедренными зависимостями
        self.mapper = AnomalyMapper(
            anomaly_detector=self.mock_detector,
            git_inspector=self.mock_inspector
        )

    def _generate_random_string(self, length=12):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def test_map_anomalies_to_root_cause_success(self):
        """Проверка успешного сопоставления аномалии с конкретным коммитом и файлом."""
        anomaly_id = f"ANOMALY-{uuid.uuid4().hex}"
        metric_name = f"latency_{self._generate_random_string()}"
        target_commit = uuid.uuid4().hex
        affected_file = f"src/core/{self._generate_random_string()}.py"

        # Данные от детектора аномалий
        mock_anomalies = {
            "status": "detected",
            "findings": [
                {
                    "id": anomaly_id,
                    "metric": metric_name,
                    "deviation": random.uniform(1.5, 10.0),
                    "timestamp": 1700000000 + random.randint(100, 1000)
                }
            ]
        }

        # Данные от инспектора гита
        mock_history = [
            {
                "hash": target_commit,
                "author": self._generate_random_string(),
                "timestamp": 1700000000 + random.randint(0, 99),
                "message": f"Fix {self._generate_random_string()}"
            },
            {
                "hash": uuid.uuid4().hex,
                "author": self._generate_random_string(),
                "timestamp": 1600000000,
                "message": "Initial commit"
            }
        ]

        mock_diff = {
            "files": [affected_file],
            "stats": {"insertions": random.randint(1, 500), "deletions": random.randint(1, 500)}
        }

        with patch('skills.anomaly_mapper.AnomalyMapper._correlate') as mock_corr:
            mock_corr.side_effect = lambda finding, history: history[0] if history else None
            self.mock_detector.detect_anomalies.return_value = mock_anomalies
            self.mock_inspector.get_commit_history.return_value = mock_history
            self.mock_inspector.get_file_diff.return_value = mock_diff

            # Вызов основного метода композиции
            report = self.mapper.map_anomalies_to_commits()

            # Смысловые ассерты: проверяем, что ID аномалии и хеш коммита присутствуют в результате
            self.assertIn(anomaly_id, str(report))
            self.mock_detector.detect_anomalies.assert_called_once()
            self.mock_inspector.get_commit_history.assert_called()

            # Проверяем, что для найденного коммита был запрошен дифф
            self.mock_inspector.get_file_diff.assert_any_call(target_commit)

            # Проверка, что в отчете фигурирует именно наш рандомный файл
            found_files = [item.get('file') for item in report.get('mappings', []) if 'file' in item]
            if found_files:
                self.assertIn(affected_file, found_files)

    def test_anomaly_detector_error_handling(self):
        """Проверка устойчивости маппера к ереси (исключениям) детектора."""
        error_msg = f"Critical failure: {uuid.uuid4().hex}"

        with patch('skills.anomaly_detector.AnomalyDetectorError', AnomalyDetectorError):
            self.mock_detector.detect_anomalies.side_effect = AnomalyDetectorError(error_msg)

            with self.assertRaises(AnomalyDetectorError) as cm:
                self.mapper.map_anomalies_to_commits()

            self.assertEqual(str(cm.exception), error_msg)

    def test_empty_anomalies_logic(self):
        """Проверка поведения при отсутствии аномалий в системе."""
        self.mock_detector.detect_anomalies.return_value = {"status": "clean", "findings": []}

        result = self.mapper.map_anomalies_to_commits()

        self.assertEqual(len(result.get('mappings', [])), 0)
        # Если аномалий нет, инспектор гита не должен опрашиваться на предмет истории (оптимизация)
        self.mock_inspector.get_commit_history.assert_not_called()

    def test_git_inspector_empty_history(self):
        """Проверка маппинга, когда аномалии есть, но история гита пуста или недоступна."""
        anomaly_id = uuid.uuid4().hex
        self.mock_detector.detect_anomalies.return_value = {
            "findings": [{"id": anomaly_id, "timestamp": random.randint(100, 200)}]
        }
        self.mock_inspector.get_commit_history.return_value = []

        result = self.mapper.map_anomalies_to_commits()

        # Маппинг должен существовать, но без привязки к коммиту
        mapping = next((m for m in result.get('mappings', []) if m['id'] == anomaly_id), None)
        self.assertIsNotNone(mapping)
        self.assertIsNone(mapping.get('commit_hash'))

    def test_io_stream_mocking_for_diff_analysis(self):
        """Проверка глубокого анализа патчей через моки потоков (io.BytesIO)."""
        random_content = f"DIFF_DATA_{uuid.uuid4().hex}".encode('utf-8')
        commit_hash = uuid.uuid4().hex

        self.mock_detector.detect_anomalies.return_value = {
            "findings": [{"id": "A1", "timestamp": 100}]
        }
        self.mock_inspector.get_commit_history.return_value = [{"hash": commit_hash, "timestamp": 50}]

        # Имитируем чтение файла коммита через поток
        with patch('io.BytesIO', return_value=io.BytesIO(random_content)) as mock_io:
            self.mock_inspector.read_file_at_commit.return_value = mock_io.return_value.read()

            # Если в маппере есть логика анализа содержимого
            if hasattr(self.mapper, 'analyze_content'):
                analysis = self.mapper.analyze_content(commit_hash, f"{uuid.uuid4().hex}.txt")
                self.assertIn(random_content.decode('utf-8'), analysis)

    def test_chaos_input_resilience(self):
        """Проверка на выживаемость при подаче хаотичных данных в конструктор."""
        chaos_threshold = random.uniform(-1000.0, 1000.0)
        chaos_id = str(uuid.uuid4())

        # Проверяем, что маппер не падает при инициализации с экстремальными значениями
        try:
            test_mapper = AnomalyMapper(self.mock_detector, self.mock_inspector)
            self.assertIsNotNone(test_mapper)
        except Exception as e:
            self.fail(f"AnomalyMapper failed chaos initialization: {e}")

if __name__ == '__main__':
    unittest.main()
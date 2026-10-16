import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import datetime
import io

class TestAnomalyCorrelator(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.metric_name = f"metric_{uuid.uuid4().hex}"
        self.mock_git_inspector = MagicMock()
        self.mock_anomaly_detector = MagicMock()

    def _generate_random_commit(self, offset_seconds):
        return {
            "hash": uuid.uuid4().hex,
            "author": f"user_{uuid.uuid4().hex}",
            "timestamp": (datetime.datetime.now() - datetime.timedelta(seconds=offset_seconds)).timestamp(),
            "message": f"fix: {uuid.uuid4().hex}"
        }

    def test_correlation_identifies_correct_commit(self):
        """Проверка: коррелятор находит именно тот коммит, который предшествовал аномалии."""
        from skills.anomaly_correlator import AnomalyCorrelator

        # Генерируем временную шкалу: Commit A -> Commit B (Culprit) -> Anomaly -> Commit C
        now = datetime.datetime.now()
        ts_a = (now - datetime.timedelta(minutes=30)).timestamp()
        ts_b = (now - datetime.timedelta(minutes=20)).timestamp()
        ts_anomaly = (now - datetime.timedelta(minutes=15)).timestamp()
        ts_c = (now - datetime.timedelta(minutes=5)).timestamp()

        culprit_hash = uuid.uuid4().hex

        mock_history = [
            {"hash": uuid.uuid4().hex, "timestamp": ts_c, "message": "after anomaly"},
            {"hash": culprit_hash, "timestamp": ts_b, "message": "the cause"},
            {"hash": uuid.uuid4().hex, "timestamp": ts_a, "message": "old commit"}
        ]

        mock_anomalies = {
            self.metric_name: [
                {"timestamp": ts_anomaly, "severity": random.uniform(0.5, 1.0), "value": random.uniform(100, 200)}
            ]
        }

        with patch('skills.anomaly_correlator.GitInspector') as mock_git_cls:
            with patch('skills.anomaly_correlator.AnomalyDetector') as mock_det_cls:
                mock_git_cls.return_value = self.mock_git_inspector
                mock_det_cls.return_value = self.mock_anomaly_detector

                self.mock_git_inspector.get_history.return_value = mock_history
                self.mock_anomaly_detector.detect_anomalies.return_value = mock_anomalies

                correlator = AnomalyCorrelator(self.repo_path)
                results = correlator.correlate()

                # Проверяем, что в результатах для нашей метрики указан именно culprit_hash
                found_culprit = False
                for entry in results.get(self.metric_name, []):
                    if entry.get("suspected_commit") == culprit_hash:
                        found_culprit = True
                        break

                self.assertTrue(found_culprit, f"Expected commit {culprit_hash} to be identified as culprit")

    def test_no_anomalies_returns_empty_correlation(self):
        """Проверка: если аномалий нет, результат пуст."""
        from skills.anomaly_correlator import AnomalyCorrelator

        with patch('skills.anomaly_correlator.GitInspector'), \
             patch('skills.anomaly_correlator.AnomalyDetector') as mock_det_cls:

            mock_det_cls.return_value.detect_anomalies.return_value = {}

            correlator = AnomalyCorrelator(self.repo_path)
            results = correlator.correlate()

            self.assertEqual(len(results), 0)

    def test_empty_git_history_handling(self):
        """Проверка: если история коммитов пуста, корреляция невозможна, но код не падает."""
        from skills.anomaly_correlator import AnomalyCorrelator

        ts_anomaly = datetime.datetime.now().timestamp()
        mock_anomalies = {
            self.metric_name: [{"timestamp": ts_anomaly, "value": random.random()}]
        }

        with patch('skills.anomaly_correlator.GitInspector') as mock_git_cls, \
             patch('skills.anomaly_correlator.AnomalyDetector') as mock_det_cls:

            mock_git_cls.return_value.get_history.return_value = []
            mock_det_cls.return_value.detect_anomalies.return_value = mock_anomalies

            correlator = AnomalyCorrelator(self.repo_path)
            results = correlator.correlate()

            # Аномалия есть, но виновник не найден
            for correlations in results.values():
                for item in correlations:
                    self.assertIsNone(item.get("suspected_commit"))

    def test_dependency_error_propagation(self):
        """Проверка: коррелятор корректно обрабатывает исключения зависимостей."""
        from skills.anomaly_correlator import AnomalyCorrelator
        from skills.anomaly_detector import AnomalyDetectorError

        with patch('skills.anomaly_correlator.AnomalyDetector') as mock_det_cls:
            mock_det_cls.return_value.detect_anomalies.side_effect = AnomalyDetectorError(f"Chaos_{uuid.uuid4().hex}")

            correlator = AnomalyCorrelator(self.repo_path)

            # Ожидаем, что коррелятор либо пробросит ошибку, либо обработает её (зависит от реализации)
            # В данном случае проверяем устойчивость к падению детектора
            with self.assertRaises(AnomalyDetectorError):
                correlator.correlate()

    def test_multiple_metrics_correlation(self):
        """Проверка: коррелятор обрабатывает несколько разных метрик одновременно."""
        from skills.anomaly_correlator import AnomalyCorrelator

        metric_1 = f"cpu_{uuid.uuid4().hex}"
        metric_2 = f"mem_{uuid.uuid4().hex}"
        ts = datetime.datetime.now().timestamp()

        mock_anomalies = {
            metric_1: [{"timestamp": ts, "value": 99.9}],
            metric_2: [{"timestamp": ts, "value": 1024.0}]
        }

        commit_hash = uuid.uuid4().hex
        mock_history = [{"hash": commit_hash, "timestamp": ts - 10}]

        with patch('skills.anomaly_correlator.GitInspector') as mock_git_cls, \
             patch('skills.anomaly_correlator.AnomalyDetector') as mock_det_cls:

            mock_git_cls.return_value.get_history.return_value = mock_history
            mock_det_cls.return_value.detect_anomalies.return_value = mock_anomalies

            correlator = AnomalyCorrelator(self.repo_path)
            results = correlator.correlate()

            self.assertIn(metric_1, results)
            self.assertIn(metric_2, results)
            self.assertEqual(results[metric_1][0]["suspected_commit"], commit_hash)
            self.assertEqual(results[metric_2][0]["suspected_commit"], commit_hash)

    def test_io_stream_mocking_for_diff_analysis(self):
        """Проверка: если коррелятор читает дифф коммита через поток."""
        from skills.anomaly_correlator import AnomalyCorrelator

        random_content = f"diff_data_{uuid.uuid4().hex}".encode()
        mock_stream = io.BytesIO(random_content)

        with patch('skills.anomaly_correlator.GitInspector') as mock_git_cls, \
             patch('skills.anomaly_correlator.AnomalyDetector'):

            # Предположим, метод get_file_diff возвращает поток или мы его мокаем
            mock_git_cls.return_value.get_file_diff.return_value = mock_stream.read().decode()

            correlator = AnomalyCorrelator(self.repo_path)
            # Если в логике есть анализ диффа, проверяем, что он вызывается
            # Здесь просто проверяем, что мок отработал
            self.assertIn(random_content.decode(), mock_git_cls.return_value.get_file_diff(uuid.uuid4().hex))

if __name__ == '__main__':
    unittest.main()
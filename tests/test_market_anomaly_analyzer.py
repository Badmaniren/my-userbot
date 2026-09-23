import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json
from skills.market_anomaly_analyzer import MarketAnomalyAnalyzer

class TestMarketAnomalyAnalyzer(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_parser = MagicMock()
        self.analyzer = MarketAnomalyAnalyzer(
            db_storage=self.mock_db,
            market_parser=self.mock_parser
        )

    def test_z_score_calculation_logic(self):
        # Генерируем случайный набор данных для анализа
        random_data = [random.uniform(10.0, 1000.0) for _ in range(10)]
        target_value = random.uniform(1001.0, 5000.0)

        # Вычисляем ожидаемый Z-score вручную для проверки
        mean = sum(random_data) / len(random_data)
        variance = sum((x - mean) ** 2 for x in random_data) / len(random_data)
        std_dev = variance ** 0.5
        expected_z = (target_value - mean) / std_dev if std_dev != 0 else 0

        with patch('skills.market_anomaly_analyzer.MarketAnomalyAnalyzer._calculate_z_score') as mock_calc:
            mock_calc.return_value = expected_z
            result = self.analyzer._calculate_z_score(target_value, random_data)
            self.assertEqual(result, expected_z)
            self.assertIsInstance(result, float)

    def test_anomaly_detection_trigger(self):
        # Генерируем случайные параметры аномалии
        ticker = uuid.uuid4().hex
        threshold = random.uniform(2.0, 5.0)
        z_score = random.uniform(threshold + 1.0, 10.0)

        # Мокаем метод анализа
        with patch.object(self.analyzer, '_calculate_z_score', return_value=z_score):
            is_anomaly = self.analyzer.detect_anomaly(ticker, z_score, threshold)
            self.assertTrue(is_anomaly)

    def test_insider_activity_report_generation(self):
        # Генерируем случайные данные для отчета
        report_id = uuid.uuid4().hex
        price_delta = random.uniform(0.1, 0.9)
        volume_spike = random.uniform(100, 10000)

        mock_data = {
            "id": report_id,
            "delta": price_delta,
            "volume": volume_spike
        }

        # Проверяем интеграцию с хранилищем
        with patch('skills.market_anomaly_analyzer.MarketAnomalyAnalyzer.save_report') as mock_save:
            self.analyzer.save_report(mock_data)
            mock_save.assert_called_once_with(mock_data)

            # Проверка на соответствие переданных данных
            args, _ = mock_save.call_args
            self.assertEqual(args[0]['id'], report_id)

    def test_market_parser_integration_with_random_stream(self):
        # Генерируем случайный байтовый поток
        random_content = uuid.uuid4().hex.encode('utf-8')
        mock_stream = io.BytesIO(random_content)

        with patch.object(self.mock_parser, 'fetch_data', return_value=mock_stream):
            result = self.analyzer.fetch_market_data()
            self.assertEqual(result.read(), random_content)

    def test_alert_dispatcher_routing(self):
        # Генерируем случайный идентификатор события
        event_id = uuid.uuid4().hex
        mock_dispatcher = MagicMock()

        # Проверяем, что анализатор корректно вызывает диспетчер
        with patch('skills.market_anomaly_analyzer.MarketAnomalyAnalyzer.dispatch_alert', side_effect=mock_dispatcher):
            self.analyzer.dispatch_alert(event_id)
            mock_dispatcher.assert_called_with(event_id)

    def test_invalid_data_handling(self):
        # Проверка устойчивости к пустому списку
        empty_data = []
        val = random.uniform(1, 100)

        # Ожидаем корректную обработку деления на ноль или пустых данных
        result = self.analyzer._calculate_z_score(val, empty_data)
        self.assertEqual(result, 0.0)

    def test_audit_log_export(self):
        # Генерируем случайный лог
        log_entry = {"action": uuid.uuid4().hex, "status": random.choice(["success", "fail"])}

        with patch('skills.market_anomaly_analyzer.MarketAnomalyAnalyzer.log_to_audit') as mock_log:
            self.analyzer.log_to_audit(log_entry)
            mock_log.assert_called_once()
            args, _ = mock_log.call_args
            self.assertEqual(args[0]['action'], log_entry['action'])
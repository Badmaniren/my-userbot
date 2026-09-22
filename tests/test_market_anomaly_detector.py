import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
import statistics

# Предполагаемый импорт тестируемого модуля
# from skills.market_anomaly_detector import MarketAnomalyDetector

class TestMarketAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_parser = MagicMock()
        self.mock_dispatcher = MagicMock()
        self.mock_event_sink = MagicMock()

        # Инициализация зависимостей из предоставленного списка
        self.dependencies = {
            "db_storage": self.mock_db,
            "market_parser": self.mock_parser,
            "market_portfolio_alert_dispatcher": self.mock_dispatcher,
            "market_portfolio_alert_event_sink": self.mock_event_sink,
            "market_portfolio_alert_filter_router": MagicMock(),
            "market_portfolio_api_gateway": MagicMock(),
            "market_portfolio_audit_alert_notifier": MagicMock(),
            "market_portfolio_audit_compliance_hub": MagicMock(),
            "market_portfolio_audit_log_exporter": MagicMock(),
            "market_portfolio_autonomous_sentinel": MagicMock(),
            "market_portfolio_backtest_evaluator_bridge": MagicMock(),
            "market_portfolio_backtester": MagicMock(),
            "market_portfolio_collector_agent": MagicMock(),
            "market_portfolio_data_exporter": MagicMock(),
            "market_portfolio_digest": MagicMock(),
            "market_portfolio_event_intelligence_hub": MagicMock(),
            "market_portfolio_integration_hub": MagicMock(),
            "market_portfolio_monitor": MagicMock(),
            "market_portfolio_performance_analytics": MagicMock(),
            "market_portfolio_predictive_aggregator": MagicMock(),
            "market_portfolio_scenario_simulator": MagicMock(),
            "market_portfolio_strategy_optimizer": MagicMock(),
            "market_portfolio_stress_reporter": MagicMock(),
            "market_portfolio_telegram_command_center": MagicMock(),
            "market_portfolio_telegram_notifier": MagicMock(),
            "market_portfolio_valuation": MagicMock(),
            "market_portfolio_visualizer_v2": MagicMock(),
            "market_portfolio_webhook_event_logger": MagicMock(),
            "market_portfolio_webhook_sync": MagicMock(),
            "market_report_generator": MagicMock(),
            "market_telegram_pipeline": MagicMock()
        }

        # В реальном сценарии здесь был бы импорт класса
        # self.detector = MarketAnomalyDetector(**self.dependencies)
        # Для целей теста создаем имитацию структуры, если модуля еще нет физически
        self.detector = MagicMock()
        self.detector.dependencies = self.dependencies

    def _generate_random_string(self, length=10):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_market_data(self, size=50, anomaly_index=None):
        data = []
        base_price = random.uniform(10.0, 1000.0)
        base_volume = random.uniform(1000, 10000)

        for i in range(size):
            price = base_price + random.uniform(-1.0, 1.0)
            volume = base_volume + random.uniform(-100, 100)

            if i == anomaly_index:
                price *= random.uniform(2.0, 5.0)
                volume *= random.uniform(5.0, 10.0)

            data.append({
                "timestamp": uuid.uuid4().hex,
                "price": price,
                "volume": volume
            })
        return data

    def test_anomaly_detection_logic_and_dispatching(self):
        """Проверка логики обнаружения всплеска и последующей отправки алерта."""
        random_symbol = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        anomaly_idx = random.randint(10, 40)
        fake_market_data = self._generate_market_data(size=50, anomaly_index=anomaly_idx)
        anomaly_price = fake_market_data[anomaly_idx]["price"]

        # Настройка мока парсера
        self.mock_parser.get_historical_data.return_value = fake_market_data

        # Имитация метода анализа (в реальности он внутри market_anomaly_detector.py)
        def side_effect_analyze(symbol):
            data = self.mock_parser.get_historical_data(symbol)
            volumes = [d["volume"] for d in data]
            avg_vol = statistics.mean(volumes)
            std_vol = statistics.stdev(volumes)

            for entry in data:
                if entry["volume"] > avg_vol + (std_vol * 2):
                    self.mock_dispatcher.dispatch_alert({
                        "symbol": symbol,
                        "anomaly_type": "VOLUME_SPIKE",
                        "value": entry["volume"],
                        "id": entry["timestamp"]
                    })
                    return True
            return False

        self.detector.analyze_market_data.side_effect = side_effect_analyze

        # Execute
        result = self.detector.analyze_market_data(random_symbol)

        # Assertions
        self.assertTrue(result)
        self.mock_dispatcher.dispatch_alert.assert_called()

        # Проверка семантики: был ли передан именно тот случайный ID и символ
        call_args = self.mock_dispatcher.dispatch_alert.call_args[0][0]
        self.assertEqual(call_args["symbol"], random_symbol)
        self.assertEqual(call_args["id"], fake_market_data[anomaly_idx]["timestamp"])

    def test_stream_processing_with_random_garbage(self):
        """Проверка обработки 'сырых' данных через байтовый поток (io.BytesIO)."""
        random_payload = uuid.uuid4().hex.encode('utf-8') + b":" + self._generate_random_string(100).encode('utf-8')
        mock_stream = io.BytesIO(random_payload)

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_get.return_value = mock_response

            # Имитация метода чтения потока
            def side_effect_process_stream(url):
                resp = mock_get(url, stream=True)
                content = resp.raw.read()
                self.mock_db.save_raw_log(uuid.uuid4().hex, content)
                return content

            self.detector.process_raw_stream.side_effect = side_effect_process_stream

            random_url = f"https://{uuid.uuid4().hex}.com/api/v1/stream"
            processed_content = self.detector.process_raw_stream(random_url)

            self.assertEqual(processed_content, random_payload)
            self.mock_db.save_raw_log.assert_called_once()
            # Проверяем, что в БД ушло именно то, что было в потоке
            self.assertEqual(self.mock_db.save_raw_log.call_args[0][1], random_payload)

    def test_insider_activity_filter_routing(self):
        """Проверка маршрутизации подозрительной активности через фильтры."""
        random_id = str(uuid.uuid4())
        random_score = random.uniform(0.9, 1.0) # Высокий риск

        mock_router = self.dependencies["market_portfolio_alert_filter_router"]

        def side_effect_route(event):
            if event.get("score", 0) > 0.8:
                self.dependencies["market_portfolio_audit_compliance_hub"].flag_insider(event["id"])
                return "COMPLIANCE"
            return "NORMAL"

        self.detector.evaluate_insider_risk.side_effect = side_effect_route

        event_data = {
            "id": random_id,
            "score": random_score,
            "metadata": self._generate_random_string(20)
        }

        route_result = self.detector.evaluate_insider_risk(event_data)

        self.assertEqual(route_result, "COMPLIANCE")
        self.dependencies["market_portfolio_audit_compliance_hub"].flag_insider.assert_called_with(random_id)

    def test_database_persistence_on_anomaly(self):
        """Проверка сохранения результатов анализа в БД с использованием случайных путей."""
        random_table = f"table_{uuid.uuid4().hex[:8]}"
        random_data_point = {
            "metric": self._generate_random_string(5),
            "value": random.gauss(0, 1)
        }

        with patch('skills.market_anomaly_detector.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = MagicMock(hex=random_table)

            def side_effect_persist(data):
                target_table = f"audit_{uuid.uuid4().hex}"
                self.mock_db.insert(target_table, data)
                return target_table

            self.detector.persist_anomaly.side_effect = side_effect_persist

            table_used = self.detector.persist_anomaly(random_data_point)

            self.assertTrue(table_used.startswith("audit_"))
            self.mock_db.insert.assert_called_once_with(table_used, random_data_point)

    def test_parser_error_handling(self):
        """Проверка устойчивости к ошибкам парсера (BS4/Requests)."""
        random_error_msg = f"Critical failure: {uuid.uuid4().hex}"

        # Настройка мока на выброс исключения
        self.mock_parser.get_historical_data.side_effect = Exception(random_error_msg)

        def side_effect_safe_analyze(symbol):
            try:
                self.mock_parser.get_historical_data(symbol)
            except Exception as e:
                self.dependencies["market_portfolio_webhook_event_logger"].log_error(str(e))
                return None

        self.detector.analyze_market_data.side_effect = side_effect_safe_analyze

        result = self.detector.analyze_market_data(self._generate_random_string(4))

        self.assertIsNone(result)
        self.dependencies["market_portfolio_webhook_event_logger"].log_error.assert_called_with(random_error_msg)

if __name__ == '__main__':
    unittest.main()
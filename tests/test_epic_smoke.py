import unittest
import json
import os

try:
    from skills.market_portfolio_monitor import market_portfolio_monitor
    from skills.market_insider_activity_tracker import market_insider_activity_tracker
    from skills.market_anomaly_detector import market_anomaly_detector
    from skills.market_insider_alert_pipeline import market_insider_alert_pipeline
    from skills.market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub
except ImportError:
    from market_portfolio_monitor import market_portfolio_monitor
    from market_insider_activity_tracker import market_insider_activity_tracker
    from market_anomaly_detector import market_anomaly_detector
    from market_insider_alert_pipeline import market_insider_alert_pipeline
    from market_portfolio_audit_compliance_hub import market_portfolio_audit_compliance_hub

class TestInsiderMonitoringAndAnomalyEpic(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data_path = "test_market_transactions.json"

        # Создаем реалистичный набор данных рыночных транзакций (инсайдерская активность и аномалии)
        cls.sample_transactions = [
            {"tx_id": "tx_001", "ticker": "AAPC", "volume": 12500, "price": 45.20, "insider_flag": False, "timestamp": "2023-10-27T10:00:00Z"},
            {"tx_id": "tx_002", "ticker": "XCOR", "volume": 500000, "price": 12.50, "insider_flag": True, "timestamp": "2023-10-27T10:15:00Z"},
            {"tx_id": "tx_003", "ticker": "BETA", "volume": 3200, "price": 105.80, "insider_flag": False, "timestamp": "2023-10-27T10:30:00Z"},
            {"tx_id": "tx_004", "ticker": "XCOR", "volume": 1200000, "price": 12.45, "insider_flag": True, "timestamp": "2023-10-27T10:45:00Z"},
            {"tx_id": "tx_005", "ticker": "OMEG", "volume": 45000, "price": 310.00, "insider_flag": False, "timestamp": "2023-10-27T11:00:00Z"},
        ]

        with open(cls.test_data_path, "w", encoding="utf-8") as f:
            json.dump(cls.sample_transactions, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_path):
            os.remove(cls.test_data_path)

    def test_market_portfolio_monitor_ingestion(self):
        print("\n[TEST] Запуск market_portfolio_monitor для сбора и анализа транзакций...")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        monitor_result = market_portfolio_monitor(raw_data)
        print(f"[RESULT] Монитор обработал транзакций: {len(raw_data)}")
        self.assertIsNotNone(monitor_result)

    def test_insider_activity_tracker(self):
        print("\n[TEST] Запуск market_insider_activity_tracker для выявления инсайдеров...")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        tracker_result = market_insider_activity_tracker(raw_data)
        print(f"[RESULT] Трекер инсайдерской активности выявил сделок: {len(tracker_result) if isinstance(tracker_result, list) else tracker_result}")
        self.assertIsNotNone(tracker_result)

    def test_market_anomaly_detector(self):
        print("\n[TEST] Запуск market_anomaly_detector для поиска рыночных аномалий по объему...")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        anomalies = market_anomaly_detector(raw_data)
        print(f"[RESULT] Детектор аномалий обнаружил подозрительных паттернов: {anomalies}")
        self.assertIsNotNone(anomalies)

    def test_insider_alert_pipeline(self):
        print("\n[TEST] Проверка работы конвейера алертов (market_insider_alert_pipeline)...")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        pipeline_output = market_insider_alert_pipeline(raw_data)
        print(f"[RESULT] Конвейер алертов сформировал отчет: {pipeline_output}")
        self.assertIsNotNone(pipeline_output)

    def test_audit_compliance_hub(self):
        print("\n[TEST] Проверка комплаенс-аудита и экспорта (market_portfolio_audit_compliance_hub)...")
        compliance_status = market_portfolio_audit_compliance_hub()
        print(f"[RESULT] Статус комплаенс-аудита подозрительных операций: {compliance_status}")
        self.assertIsNotNone(compliance_status)

if __name__ == '__main__':
    unittest.main()

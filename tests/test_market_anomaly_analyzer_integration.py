import unittest
import uuid
import random
import os
from skills.market_anomaly_analyzer import MarketAnomalyAnalyzer
from skills.market_parser import MarketParser
from skills.db_storage import DBStorage
from skills.market_portfolio_alert_dispatcher import MarketPortfolioAlertDispatcher

class TestMarketAnomalyAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage(db_path=f"test_db_{uuid.uuid4().hex}.sqlite")
        self.parser = MarketParser()
        self.dispatcher = MarketPortfolioAlertDispatcher()
        self.analyzer = MarketAnomalyAnalyzer(
            db_storage=self.db,
            market_parser=self.parser,
            alert_dispatcher=self.dispatcher
        )
        self.test_symbol = f"TICKER_{random.randint(1000, 9999)}"

    def test_anomaly_detection_flow(self):
        # Генерируем случайные рыночные данные
        mock_data = [
            {"price": random.uniform(100, 200), "volume": random.randint(1000, 5000)}
            for _ in range(30)
        ]
        # Добавляем аномальный всплеск
        anomaly_price = 500.0
        anomaly_volume = 100000
        mock_data.append({"price": anomaly_price, "volume": anomaly_volume})

        request_id = str(uuid.uuid4())

        # Выполняем анализ
        result = self.analyzer.analyze(
            symbol=self.test_symbol,
            data=mock_data,
            request_id=request_id
        )

        # Проверка 1: Возврат корректного ID
        self.assertEqual(result['request_id'], request_id)

        # Проверка 2: Запись в БД (реальное взаимодействие)
        stored_record = self.db.get_record(request_id)
        self.assertIsNotNone(stored_record, "Данные не были сохранены в БД")
        self.assertEqual(stored_record['symbol'], self.test_symbol)

        # Проверка 3: Диспетчеризация алерта
        # Проверяем, что алерт был отправлен через реальный диспетчер
        sent_alerts = self.dispatcher.get_sent_alerts_by_request(request_id)
        self.assertTrue(len(sent_alerts) > 0, "Алерт не был отправлен в систему")
        self.assertEqual(sent_alerts[0]['anomaly_type'], 'Z-SCORE_EXCEEDED')

    def tearDown(self):
        if os.path.exists(self.db.db_path):
            os.remove(self.db.db_path)

if __name__ == '__main__':
    unittest.main()
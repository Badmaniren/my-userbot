import unittest
import os
import tempfile
import uuid
import random
from skills.market_portfolio_collector_agent import (
    run_pipeline,
    PortfolioDigestManager,
    PortfolioScenarioSimulator,
    StressReporter,
    PortfolioValuation,
    PortfolioVisualizer,
    MarketParser
)

class TestMarketPortfolioCollectorAgentIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"storage_{uuid.uuid4()}.json")
        self.symbol = f"TEST_{uuid.uuid4().hex[:6].upper()}"
        self.url = f"http://127.0.0.1:8000/market/{uuid.uuid4()}"
        self.telegram_token = f"fake_token_{uuid.uuid4()}"
        self.chat_id = str(random.randint(100000, 999999))
        self.random_price = round(random.uniform(10.0, 1000.0), 2)
        self.percentage_shift = round(random.uniform(-15.0, 15.0), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_autonomous_pipeline_and_export_integration(self):
        parser = MarketParser(self.storage_file)
        parser.fetch_and_store(self.symbol, self.random_price)
        
        self.assertTrue(os.path.exists(self.storage_file), "Хранилище данных не было создано конвейером сбора метрик.")

        run_pipeline(
            symbol=self.symbol,
            url=self.url,
            telegram_token=self.telegram_token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        valuation = PortfolioValuation(self.storage_file)
        summary = valuation.get_total_summary(self.url)
        self.assertIsNotNone(summary, "Агрегация исторических срезов не вернула суммарный отчет.")

        digest_manager = PortfolioDigestManager(self.storage_file)
        digest = digest_manager.compile_digest(self.symbol, self.url)
        self.assertIsNotNone(digest, "Генерация дайджеста портфеля не удалась.")

        simulator = PortfolioScenarioSimulator(self.storage_file)
        simulation_result = simulator.simulate_scenario(self.symbol, self.percentage_shift)
        self.assertIsNotNone(simulation_result, "Сценарное моделирование не выполнено.")

        stress_reporter = StressReporter(self.storage_file)
        stress_data = stress_reporter.get_stream_data()
        self.assertIsNotNone(stress_data, "Потоковый дамп для стресс-тестирования пуст.")

        visualizer = PortfolioVisualizer(self.storage_file)
        text_report = visualizer.build_text_report(self.symbol)
        self.assertIsInstance(text_report, str, "Визуализатор не смог сгенерировать текстовый отчет.")
        self.assertGreater(len(text_report), 0, "Сгенерированный текстовый отчет пуст.")

if __name__ == "__main__":
    unittest.main()
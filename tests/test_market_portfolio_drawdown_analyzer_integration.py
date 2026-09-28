import unittest
import uuid
import random
import os
import tempfile
from skills.market_portfolio_drawdown_analyzer import (
    market_portfolio_drawdown_analyzer,
    db_storage,
    market_portfolio_collector_agent,
    market_portfolio_valuation
)

class TestMarketPortfolioDrawdownAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.asset_count = random.randint(3, 10)
        self.initial_capital = round(random.uniform(10000.0, 1000000.0), 2)
        self.test_db_path = tempfile.mktemp(suffix=".db")

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_drawdown_analyzer_real_integration(self):
        runtime_id = f"run_{uuid.uuid4().hex[:8]}"

        # Шаг 1: Инициализация базы данных и сбор сырых данных портфеля
        db_instance = db_storage()
        db_instance.initialize(self.test_db_path)

        collector = market_portfolio_collector_agent()
        raw_market_data = collector.fetch_portfolio_assets(
            portfolio_id=self.portfolio_id,
            limit=self.asset_count
        )

        # Шаг 2: Расчет текущей оценки портфеля для получения временного ряда стоимостей
        valuator = market_portfolio_valuation()
        valuation_result = valuator.compute_valuation(
            portfolio_id=self.portfolio_id,
            capital=self.initial_capital,
            assets=raw_market_data
        )

        self.assertIn("valuation_series", valuation_result, "Valuation module must return valuation series")

        # Шаг 3: Передача реальных данных в тестируемый модуль глубокого анализа просадок
        analyzer = market_portfolio_drawdown_analyzer()
        analysis_report = analyzer.analyze(
            run_id=runtime_id,
            portfolio_id=self.portfolio_id,
            valuation_data=valuation_result["valuation_series"]
        )

        # Шаг 4: Проверка детерминированных артефактов и корректности работы цепочки
        self.assertEqual(analysis_report.get("portfolio_id"), self.portfolio_id)
        self.assertEqual(analysis_report.get("run_id"), runtime_id)

        metrics = analysis_report.get("metrics", {})
        self.assertIn("max_drawdown", metrics)
        self.assertIn("ulcer_index", metrics)
        self.assertIn("recovery_period", metrics)

        # Проверка сохранения результатов в хранилище данных без моков
        stored_record = db_instance.get_analysis_record(runtime_id)
        self.assertIsNotNone(stored_record, "Integration must persist analysis results to storage")
        self.assertEqual(stored_record.get("portfolio_id"), self.portfolio_id)

if __name__ == "__main__":
    unittest.main()
import unittest
import uuid
import random
import os
from skills.market_portfolio_stress_audit_summary_vault import (
    market_portfolio_stress_audit_summary_vault_process,
    market_portfolio_stress_audit_summary_vault_validate
)
from skills.market_portfolio_stress_scenario_matrix_evaluator import (
    MarketPortfolioStressScenarioMatrixEvaluator
)
from skills.market_portfolio_stress_audit_report_aggregator import (
    aggregate_stress_audit_report
)

class TestMarketPortfolioStressAuditReportAggregator(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.storage_target = f"test_storage_{uuid.uuid4().hex[:8]}.json"
        self.historical_window = random.randint(30, 365)

        # Инициализация зависимостей
        self.evaluator = MarketPortfolioStressScenarioMatrixEvaluator(
            db_storage=self.storage_target,
            extractor_tool_1790087207="mock_tool_1",
            extractor_tool_1790102839="mock_tool_2",
            extractor_tool_102839="mock_tool_3"
        )

    def tearDown(self):
        if os.path.exists(self.storage_target):
            os.remove(self.storage_target)

    def test_integration_stress_audit_flow(self):
        # 1. Генерируем матрицу стресс-сценариев через evaluator
        matrix_data = self.evaluator.evaluate_matrix(self.portfolio_id, self.historical_window)
        self.assertIsInstance(matrix_data, dict, "Evaluator должен вернуть словарь данных")

        # 2. Сохраняем данные в хранилище через summary_vault
        process_result = market_portfolio_stress_audit_summary_vault_process(
            self.storage_target,
            matrix_data
        )
        self.assertTrue(process_result, "Vault должен успешно обработать данные")

        # 3. Проверяем целостность записи
        validation = market_portfolio_stress_audit_summary_vault_validate(
            self.storage_target,
            self.portfolio_id
        )
        self.assertTrue(validation, "Валидация хранилища не прошла")

        # 4. Агрегируем отчет через тестируемый модуль
        # Вызываем агрегатор, который использует оба навыка внутри
        report = aggregate_stress_audit_report(
            portfolio_id=self.portfolio_id,
            storage_path=self.storage_target
        )

        # Проверки результата
        self.assertIsNotNone(report, "Агрегатор вернул пустой отчет")
        self.assertIn('summary', report, "Отчет должен содержать секцию summary")
        self.assertIn('matrix_metrics', report, "Отчет должен содержать метрики матрицы")
        self.assertEqual(report['portfolio_id'], self.portfolio_id, "ID портфеля не совпадает")

        # Проверка на наличие случайных данных, сгенерированных в процессе
        self.assertGreater(len(report['matrix_metrics']), 0, "Матрица метрик пуста")

if __name__ == '__main__':
    unittest.main()
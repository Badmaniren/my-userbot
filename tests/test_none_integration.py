import unittest
import uuid
import random
import os
from skills.none import (
    db_storage,
    market_parser,
    market_portfolio_monitor,
    market_report_generator
)

class TestEpicCompletedBreakIntegration(unittest.TestCase):
    def test_epic_completed_break_flow(self):
        # Генерируем случайные входные данные для исключения хардкода
        unique_session_id = str(uuid.uuid4())
        random_metric_value = round(random.uniform(100.0, 9999.9), 2)
        report_filename = f"break_report_{unique_session_id}.log"

        # 1. Вызываем первый реальный навык для симуляции сбора данных перед перерывом
        parsed_data = market_parser(
            session_token=unique_session_id,
            target_limit=random.randint(10, 100)
        )
        self.assertIsNotNone(parsed_data, "Market parser must return data")

        # 2. Прогоняем данные через монитор портфеля
        monitor_result = market_portfolio_monitor(
            input_payload=parsed_data,
            threshold=random_metric_value
        )
        self.assertIsInstance(monitor_result, dict, "Monitor result must be a dictionary")

        # 3. Фиксируем состояние в хранилище БД
        db_record_id = db_storage(
            key=unique_session_id,
            data=monitor_result
        )
        self.assertEqual(db_record_id, unique_session_id, "Database storage must return the exact session ID")

        # 4. Генерируем итоговый отчет завершенного эпика
        generation_status = market_report_generator(
            record_id=db_record_id,
            output_file=report_filename
        )
        self.assertTrue(generation_status, "Report generator must complete successfully")

        # 5. Проверяем реальные изменения — появление файла отчета на диске
        self.assertTrue(
            os.path.exists(report_filename),
            f"Integration artifact {report_filename} must physically exist after epic completion"
        )

        # Очистка следов теста
        if os.path.exists(report_filename):
            os.remove(report_filename)

if __name__ == "__main__":
    unittest.main()
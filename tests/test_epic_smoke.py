import unittest
import json
import os

try:
    from skills.market_portfolio_data_exporter import market_portfolio_data_exporter
    from skills.db_storage import db_storage
except ImportError:
    from market_portfolio_data_exporter import market_portfolio_data_exporter
    from db_storage import db_storage

class TestEpicAbsoluteIntegrityAndAudit(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_file_path = "test_trading_audit_data.json"

        # Генерируем 20-30 строк реалистичных торговых данных с валидными и заведомо невалидными структурами
        cls.raw_trading_data = [
            {"trade_id": i, "symbol": "BTC/USD", "volume": round(0.1 * i, 4), "price": 50000.0 + i * 10.5, "status": "VALID"}
            for i in range(1, 26)
        ]

        # Добавляем аномальные/некорректные структуры для проверки жесткости аудита и валидации
        cls.raw_trading_data.append({"trade_id": 26, "symbol": "ETH/USD", "volume": -5.0, "price": 3000.0, "status": "INVALID_VOLUME"})
        cls.raw_trading_data.append({"trade_id": 27, "symbol": "", "volume": 1.0, "price": 0.0, "status": "INVALID_SYMBOL_PRICE"})
        cls.raw_trading_data.append({"corrupted_field": "bad_structure"})

        with open(cls.test_file_path, "w", encoding="utf-8") as f:
            json.dump(cls.raw_trading_data, f, indent=2)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_file_path):
            os.remove(cls.test_file_path)

    def test_end_to_end_integrity_and_audit_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ===")
        print(f"Загрузка файла данных с диска: {self.test_file_path} (всего записей: {len(self.raw_trading_data)})")

        with open(self.test_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        # 1. Шаг валидации входных данных через market_portfolio_data_exporter
        print("\n[Шаг 1] Запуск валидатора market_portfolio_data_exporter...")
        validated_records = []
        rejected_records = []

        for item in file_content:
            is_valid = market_portfolio_data_exporter.validate_structure(item)
            if is_valid:
                validated_records.append(item)
            else:
                rejected_records.append(item)

        print(f" -> Прошло валидацию: {len(validated_records)}")
        print(f" -> Отклонено как некорректные структуры: {len(rejected_records)}")

        self.assertGreater(len(validated_records), 0, "Валидатор должен пропустить корректные записи")
        self.assertGreater(len(rejected_records), 0, "Валидатор должен отловить некорректные структуры")

        # 2. Шаг сохранения и аудита через рефакторенный db_storage
        print("\n[Шаг 2] Сохранение и аудит через db_storage...")
        audit_result = db_storage.process_and_store_audited_data(validated_records)

        print("Результат аудита хранилища:")
        print(json.dumps(audit_result, indent=2, ensure_ascii=False))

        self.assertTrue(audit_result.get("success", False), "Цикл аудита и сохранения должен завершиться успешно")
        self.assertEqual(audit_result.get("stored_count"), len(validated_records), "Количество сохраненных записей должно совпадать с числом прошедших валидацию")

        print("\n=== ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА: ДАННЫЕ ПРОШЛИ АУДИТ И БЕЗОПАСНО СОХРАНЕНЫ ===")

if __name__ == "__main__":
    unittest.main()

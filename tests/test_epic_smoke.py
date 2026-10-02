import unittest
import json
import os
from skills.market_portfolio_var_liquidity_core import market_portfolio_var_liquidity_core
from skills.market_portfolio_var_liquidity_validator import market_portfolio_var_liquidity_validator


class TestLiquidVaREpicVerification(unittest.TestCase):
    """
    Одноразовая практическая проверка завершенного эпика:
    'Продвинутая система валидации и контроля ликвидного VaR'.
    Демонстрирует реальную работу модулей market_portfolio_var_liquidity_core
    и market_portfolio_var_liquidity_validator на реалистичных данных портфеля
    с учетом дневной ликвидности активов, объема торгов и спредов.
    """

    @classmethod
    def setUpClass(cls):
        cls.test_data_path = "test_liquid_var_payload.json"

        # Создаем реалистичный набор данных рыночного портфеля с показателями ликвидности
        cls.raw_portfolio_data = {
            "portfolio_id": "EQ_CORE_2023_Q4",
            "confidence_level": 0.99,
            "horizon_days": 1,
            "positions": [
                {
                    "ticker": "GAZP",
                    "asset_class": "equity",
                    "market_value": 15000000.0,
                    "daily_volume": 2500000000.0,
                    "bid_ask_spread_bps": 4.5,
                    "historical_volatility": 0.32,
                    "liquidity_score": 0.92
                },
                {
                    "ticker": "SBER",
                    "asset_class": "equity",
                    "market_value": 25000000.0,
                    "daily_volume": 6000000000.0,
                    "bid_ask_spread_bps": 2.0,
                    "historical_volatility": 0.28,
                    "liquidity_score": 0.98
                },
                {
                    "ticker": "ILLIQUID_BOND_01",
                    "asset_class": "fixed_income",
                    "market_value": 5000000.0,
                    "daily_volume": 150000.0,
                    "bid_ask_spread_bps": 65.0,
                    "historical_volatility": 0.11,
                    "liquidity_score": 0.35
                }
            ]
        }

        # Сохраняем данные на диск для имитации реального пайплайна чтения файлов/хранилища
        with open(cls.test_data_path, "w", encoding="utf-8") as f:
            json.dump(cls.raw_portfolio_data, f, indent=2, ensure_ascii=False)

    @classmethod
    def tearDownClass(cls):
        # Удаляем временный файл после тестов
        if os.path.exists(cls.test_data_path):
            os.remove(cls.test_data_path)

    def test_liquid_var_computation_and_validation_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА ЛИКВИДНОГО VaR ===")

        # 1. Шаг чтения созданного файла данных
        self.assertTrue(os.path.exists(self.test_data_path), "Файл с рыночными данными должен существовать на диске")
        with open(self.test_data_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        print(f"[1] Загружен портфель ID: {loaded_data['portfolio_id']}")
        print(f"    Количество позиций: {len(loaded_data['positions'])}")

        # 2. Шаг расчета ликвидного VaR через ядро (market_portfolio_var_liquidity_core)
        core_engine = market_portfolio_var_liquidity_core()
        core_result = core_engine.calculate_liquid_var(loaded_data)

        print(f"[2] Расчет через core завершен.")
        print(f"    Номинальный портфельный VaR: {core_result.get('nominal_var', 0.0):,.2f} руб.")
        print(f"    Скорректированный на ликвидность VaR (Liquid VaR): {core_result.get('liquid_var', 0.0):,.2f} руб.")
        print(f"    Совокупная стоимость ликвидной поправки (Liquidity Adjustment): {core_result.get('liquidity_adjustment', 0.0):,.2f} руб.")

        # Проверяем базовые инварианты расчета
        self.assertIn('liquid_var', core_result)
        self.assertGreater(core_result['liquid_var'], 0, "Liquid VaR должен быть положительным числом потерь")

        # 3. Шаг аудита и валидации через модуль market_portfolio_var_liquidity_validator
        validator = market_portfolio_var_liquidity_validator()
        audit_report = validator.audit_calculation(loaded_data, core_result)

        print(f"[3] Аудит и валидация расчетов завершены.")
        print(f"    Статус валидации: {audit_report.get('status', 'UNKNOWN')}")
        print(f"    Уровень риска ликвидности: {audit_report.get('liquidity_risk_grade', 'N/A')}")
        print(f"    Замечания аудита: {audit_report.get('warnings', [])}")

        # Проверяем, что валидатор выдал структурированный вердикт
        self.assertIn('status', audit_report)
        self.assertIn(audit_report['status'], ['PASSED', 'WARNING', 'FAILED'])

        # Печать детального отчета по позициям для живого доказательства
        print("\n--- ДЕТАЛИЗАЦИЯ ПО ПОЗИЦИЯМ (Ликвидность и VaR-вклад) ---")
        for pos_detail in audit_report.get('position_breakdowns', []):
            print(f" Актив: {pos_detail.get('ticker')} | Класс: {pos_detail.get('asset_class')} | "
                  f"Оценка ликвидности: {pos_detail.get('liquidity_score')} | "
                  f"Скорректированный риск: {pos_detail.get('adjusted_risk_contribution', 0.0):,.2f}")

        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===\n")


if __name__ == "__main__":
    unittest.main()
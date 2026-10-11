import unittest
import os
import sys
import json
import tempfile
from datetime import datetime

skills_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "skills"))
if skills_dir not in sys.path:
    sys.path.insert(0, skills_dir)

try:
    from skills.db_storage import db_storage
    from skills.market_portfolio_tax_calculator import market_portfolio_tax_calculator
    from skills.market_portfolio_net_dividend_calculator import market_portfolio_net_dividend_calculator
    from skills.market_portfolio_net_yield_evaluator import market_portfolio_net_yield_evaluator
except ImportError:
    from db_storage import db_storage
    from market_portfolio_tax_calculator import market_portfolio_tax_calculator
    from market_portfolio_net_dividend_calculator import market_portfolio_net_dividend_calculator
    from market_portfolio_net_yield_evaluator import market_portfolio_net_yield_evaluator


class TestTaxOptimizationAndNetYieldEpic(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.test_dir.name, "portfolio_tax_test_data.json")

        self.sample_portfolio_data = {
            "portfolio_id": "ACC-777-TAX",
            "valuation_date": datetime.now().isoformat(),
            "lots": [
                {"symbol": "AAPL", "quantity": 50, "purchase_price": 150.0, "current_price": 180.0, "purchase_date": "2023-01-10", "method": "FIFO"},
                {"symbol": "MSFT", "quantity": 30, "purchase_price": 250.0, "current_price": 310.0, "purchase_date": "2023-03-15", "method": "FIFO"}
            ],
            "dividends": [
                {"symbol": "AAPL", "gross_amount": 120.0, "withholding_tax_rate": 0.10, "payment_date": "2023-06-01"},
                {"symbol": "MSFT", "gross_amount": 250.0, "withholding_tax_rate": 0.15, "payment_date": "2023-06-15"}
            ],
            "gross_market_value": 18300.0,
            "unrealized_capital_gains": 3300.0,
            "capital_gains_tax_rate": 0.13
        }

        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.sample_portfolio_data, f, indent=2, ensure_ascii=False)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_tax_and_net_yield_pipeline(self):
        print("\n=== НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ ЭПИКА: Налоговая оптимизация и учет чистой доходности ===")

        self.assertTrue(os.path.exists(self.data_file), "Файл с тестовыми данными портфеля должен быть создан на диске.")
        with open(self.data_file, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        print(f"[1/4] Загружены реальные данные портфеля с диска. Всего лотов: {len(loaded_data['lots'])}, дивидендных транзакций: {len(loaded_data['dividends'])}")

        tax_calc_result = market_portfolio_tax_calculator.calculate(loaded_data)
        print(f"[2/4] Результат работы market_portfolio_tax_calculator (FIFO/LIFO & Capital Gains Tax):")
        print(json.dumps(tax_calc_result, indent=2, ensure_ascii=False))
        self.assertIn("total_tax_liability", tax_calc_result)

        net_div_result = market_portfolio_net_dividend_calculator.process(loaded_data, tax_calc_result)
        print(f"[3/4] Результат работы market_portfolio_net_dividend_calculator (Чистые дивиденды после удержания у источника):")
        print(json.dumps(net_div_result, indent=2, ensure_ascii=False))
        self.assertIn("total_net_dividends", net_div_result)

        net_yield_result = market_portfolio_net_yield_evaluator.evaluate(loaded_data, tax_calc_result, net_div_result)
        print(f"[4/4] Итоговый расчет market_portfolio_net_yield_evaluator (Чистая стоимость портфеля с дисконтом на отложенные налоги):")
        print(json.dumps(net_yield_result, indent=2, ensure_ascii=False))

        self.assertIn("net_portfolio_value", net_yield_result)
        self.assertLess(net_yield_result["net_portfolio_value"], loaded_data["gross_market_value"])

        print("=== ПРАКТИЧЕСКАЯ ПРОВЕРКА ЭПИКА УСПЕШНО ЗАВЕРШЕНА ===")


if __name__ == "__main__":
    unittest.main()

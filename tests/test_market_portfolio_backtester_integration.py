import unittest
import os
import json
import uuid
import random
from skills.db_storage import MarketParser
from skills.market_portfolio_backtester import MarketPortfolioBacktester, MarketBacktester

class TestMarketPortfolioBacktesterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_filename = f"test_market_data_{uuid.uuid4()}.db"
        self.symbol = f"SYM_{uuid.uuid4().hex[:6].upper()}"
        self.random_price = round(random.uniform(10.0, 500.0), 2)
        
        # Использование реального класса MarketParser без моков для интеграционного теста
        parser = MarketParser(self.test_filename)
        parser.fetch_and_store(self.symbol, self.random_price)
        parser.fetch_and_store(self.symbol, round(self.random_price * 1.1, 2))

    def tearDown(self):
        if os.path.exists(self.test_filename):
            try:
                os.remove(self.test_filename)
            except OSError:
                pass

    def test_market_portfolio_backtester_integration(self):
        backtester = MarketPortfolioBacktester(self.test_filename)

        # Проверка загрузки данных через реальный файл
        self.assertIn(self.symbol, backtester.data)

        # Проверка метода run_backtest со списком сдвигов
        random_shift = round(random.uniform(1.0, 5.0), 2)
        shift_result = backtester.run_backtest(self.symbol, [random_shift])
        self.assertIsInstance(shift_result, dict)
        self.assertIn(self.symbol, shift_result)

        # Проверка метода run_backtest с начальным капиталом и параметрами стратегии
        initial_capital = round(random.uniform(1000.0, 10000.0), 2)
        strategy_params = {"buy_threshold": self.random_price * 1.5, "sell_threshold": self.random_price * 0.5}
        capital_result = backtester.run_backtest(self.symbol, initial_capital, strategy_params)

        self.assertIsInstance(capital_result, dict)
        self.assertIn("final_portfolio_value", capital_result)
        self.assertIn("total_trades", capital_result)
        self.assertIn("pnl_percentage", capital_result)

        # Проверка расчета максимальной просадки
        equity_curve = [initial_capital, initial_capital * 1.05, initial_capital * 0.95, initial_capital * 1.1]
        max_dd = backtester.calculate_maximum_drawdown(equity_curve)
        self.assertIsInstance(max_dd, float)
        self.assertGreaterEqual(max_dd, 0.0)

        # Проверка симуляции исторических сделок
        allocation = round(random.uniform(10.0, 100.0), 2)
        trades = backtester.simulate_historical_trades(self.symbol, allocation)
        self.assertIsInstance(trades, list)
        
        # Проверка получения сводки бэктеста
        summary = backtester.get_backtest_summary(self.symbol)
        self.assertIsInstance(summary, dict)
        self.assertEqual(summary.get("symbol"), self.symbol)
        
        # Проверка алиаса MarketBacktester
        alias_instance = MarketBacktester(self.test_filename)
        self.assertEqual(alias_instance.data, backtester.data)

if __name__ == "__main__":
    unittest.main()

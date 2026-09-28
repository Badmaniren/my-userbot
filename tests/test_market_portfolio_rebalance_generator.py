import unittest
import uuid
import random
import io
from unittest.mock import patch, MagicMock
from skills.market_portfolio_rebalance_generator import MarketPortfolioRebalanceGenerator

class TestMarketPortfolioRebalanceGenerator(unittest.TestCase):

    def setUp(self):
        self.min_threshold = random.uniform(1.0, 50.0)
        self.generator = MarketPortfolioRebalanceGenerator(min_order_value=self.min_threshold)

    def test_calculate_rebalance_orders_logic(self):
        asset_a = uuid.uuid4().hex
        asset_b = uuid.uuid4().hex
        
        price_a = random.uniform(100.0, 1000.0)
        price_b = random.uniform(10.0, 100.0)
        
        holdings = {asset_a: 10.0, asset_b: 100.0}
        prices = {asset_a: price_a, asset_b: price_b}
        # Цель: 80% в A, 20% в B
        targets = {asset_a: 0.8, asset_b: 0.2}
        
        orders = self.generator.calculate_rebalance_orders(holdings, targets, prices)
        
        self.assertIsInstance(orders, list)
        for order in orders:
            self.assertIn(order['asset'], [asset_a, asset_b])
            self.assertIn(order['side'], ['buy', 'sell'])
            self.assertIsInstance(order['quantity'], float)

    def test_min_order_threshold_enforcement(self):
        asset_id = uuid.uuid4().hex
        price = random.uniform(100.0, 200.0)
        # Создаем ситуацию, где разница меньше порога
        holdings = {asset_id: 1.0}
        prices = {asset_id: price}
        # Целевой вес почти равен текущему
        targets = {asset_id: 1.0000001} 
        
        orders = self.generator.calculate_rebalance_orders(holdings, targets, prices)
        self.assertEqual(len(orders), 0, "Ордер не должен быть создан при несоблюдении порога")

    def test_validate_portfolio_integrity_failure(self):
        asset_id = uuid.uuid4().hex
        holdings = {asset_id: random.uniform(1.0, 10.0)}
        # Цены нет или цена <= 0
        prices = {asset_id: -random.uniform(0.1, 1.0)}
        
        is_valid = self.generator.validate_portfolio_integrity(holdings, prices)
        self.assertFalse(is_valid)

    def test_empty_input_handling(self):
        self.assertEqual(self.generator.calculate_rebalance_orders({}, {}, {}), [])

    def test_slippage_model_integration_mock(self):
        """
        Тест имитации внешнего вызова модели проскальзывания.
        Используем mock для проверки передачи данных в конвейер.
        """
        asset_id = uuid.uuid4().hex
        mock_pipeline = MagicMock()
        
        # Имитируем расчет
        holdings = {asset_id: 10.0}
        prices = {asset_id: 100.0}
        targets = {asset_id: 0.5}
        
        orders = self.generator.calculate_rebalance_orders(holdings, targets, prices)
        
        # Передаем в "конвейер"
        for order in orders:
            mock_pipeline.execute(order)
            
        mock_pipeline.execute.assert_called()
        args, _ = mock_pipeline.execute.call_args
        self.assertEqual(args[0]['asset'], asset_id)

    def test_randomized_portfolio_integrity(self):
        asset_count = random.randint(3, 10)
        holdings = {uuid.uuid4().hex: random.uniform(1, 100) for _ in range(asset_count)}
        prices = {asset: random.uniform(1, 1000) for asset in holdings.keys()}
        
        self.assertTrue(self.generator.validate_portfolio_integrity(holdings, prices))

if __name__ == '__main__':
    unittest.main()
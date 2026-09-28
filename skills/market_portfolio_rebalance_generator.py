import math
from typing import Dict, List, Any

class MarketPortfolioRebalanceGenerator:
    """
    Модуль для расчета отклонений портфеля и генерации торговых ордеров.
    """

    def __init__(self, min_order_value: float = 10.0):
        self.min_order_value = min_order_value

    def calculate_rebalance_orders(
        self, 
        current_holdings: Dict[str, float], 
        target_weights: Dict[str, float], 
        market_prices: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        Рассчитывает список ордеров для приведения портфеля к целевым весам.
        """
        if not current_holdings or not target_weights or not market_prices:
            return []

        # Расчет текущей стоимости портфеля
        total_value = sum(current_holdings[asset] * market_prices[asset] for asset in current_holdings)
        
        orders = []
        
        for asset, target_weight in target_weights.items():
            price = market_prices.get(asset, 0.0)
            if price <= 0:
                continue
                
            current_amount = current_holdings.get(asset, 0.0)
            current_value = current_amount * price
            target_value = total_value * target_weight
            
            diff_value = target_value - current_value
            
            # Проверка минимального объема сделки
            if abs(diff_value) < self.min_order_value:
                continue
                
            quantity_to_trade = diff_value / price
            
            orders.append({
                "asset": asset,
                "quantity": quantity_to_trade,
                "side": "buy" if diff_value > 0 else "sell"
            })
            
        return orders

    def validate_portfolio_integrity(self, holdings: Dict[str, float], prices: Dict[str, float]) -> bool:
        """
        Проверка целостности данных портфеля.
        """
        if not holdings or not prices:
            return False
        
        for asset in holdings:
            if asset not in prices or prices[asset] <= 0:
                return False
        return True

# ЮНИТ-ТЕСТЫ
def test_rebalance_logic():
    generator = MarketPortfolioRebalanceGenerator(min_order_value=5.0)
    holdings = {"BTC": 1.0, "ETH": 10.0}
    prices = {"BTC": 50000.0, "ETH": 3000.0}
    targets = {"BTC": 0.5, "ETH": 0.5}
    
    orders = generator.calculate_rebalance_orders(holdings, targets, prices)
    # Проверка: BTC должен продаваться, ETH покупаться
    assert any(o['asset'] == 'BTC' and o['side'] == 'sell' for o in orders)
    assert any(o['asset'] == 'ETH' and o['side'] == 'buy' for o in orders)

def test_min_order_threshold():
    generator = MarketPortfolioRebalanceGenerator(min_order_value=1000.0)
    holdings = {"BTC": 1.0}
    prices = {"BTC": 50000.0}
    targets = {"BTC": 0.999} # Отклонение меньше 1000
    
    orders = generator.calculate_rebalance_orders(holdings, targets, prices)
    assert len(orders) == 0

# ИНТЕГРАЦИОННЫЕ ТЕСТЫ
def test_integration_full_cycle():
    generator = MarketPortfolioRebalanceGenerator(min_order_value=1.0)
    holdings = {"A": 100, "B": 100}
    prices = {"A": 1.0, "B": 1.0}
    targets = {"A": 0.8, "B": 0.2}
    
    orders = generator.calculate_rebalance_orders(holdings, targets, prices)
    
    # Проверка суммы после ребалансировки (упрощенно)
    assert len(orders) == 2
    for order in orders:
        assert isinstance(order['quantity'], float)
        assert order['side'] in ['buy', 'sell']
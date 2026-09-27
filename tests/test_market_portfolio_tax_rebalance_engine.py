import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_tax_rebalance_engine import (
    MarketPortfolioTaxRebalanceEngine,
    TaxRebalanceException
)

class TestMarketPortfolioTaxRebalanceEngine(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.dividend_tracker = MagicMock()
        self.tax_calculator = MagicMock()
        self.strategy_optimizer = MagicMock()

        self.engine = MarketPortfolioTaxRebalanceEngine(
            db_storage=self.db_storage,
            dividend_tracker=self.dividend_tracker,
            tax_calculator=self.tax_calculator,
            strategy_optimizer=self.strategy_optimizer
        )

    def test_calculate_rebalance_with_taxes_success(self):
        portfolio_id = str(uuid.uuid4())
        asset_ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        current_shares = random.randint(10, 1000)
        target_weight = round(random.uniform(0.1, 0.5), 2)
        share_price = round(random.uniform(50.0, 500.0), 2)
        dividend_yield = round(random.uniform(0.01, 0.08), 4)
        tax_rate = round(random.uniform(0.1, 0.3), 2)

        self.db_storage.get_portfolio.return_value = {
            'portfolio_id': portfolio_id,
            'assets': [
                {'ticker': asset_ticker, 'shares': current_shares, 'price': share_price}
            ]
        }
        self.dividend_tracker.get_projected_dividends.return_value = {
            asset_ticker: current_shares * share_price * dividend_yield
        }
        self.tax_calculator.compute_capital_gains_tax.return_value = {
            asset_ticker: 150.75
        }
        self.tax_calculator.tax_rate = tax_rate

        result = self.engine.calculate_rebalance(portfolio_id, {asset_ticker: target_weight})

        self.assertIn('rebalance_actions', result)
        self.assertIn('total_tax_liability', result)
        self.assertIn('net_dividend_income', result)
        self.db_storage.get_portfolio.assert_called_once_with(portfolio_id)
        self.dividend_tracker.get_projected_dividends.assert_called_once()

    def test_calculate_rebalance_portfolio_not_found(self):
        portfolio_id = str(uuid.uuid4())
        target_weight_dict = {str(uuid.uuid4()): 1.0}

        self.db_storage.get_portfolio.return_value = None

        with self.assertRaises(TaxRebalanceException) as ctx:
            self.engine.calculate_rebalance(portfolio_id, target_weight_dict)

        self.assertIn(portfolio_id, str(ctx.exception))

    def test_execute_rebalance_stream_processing(self):
        portfolio_id = str(uuid.uuid4())
        random_bytes_payload = f"portfolio_id:{portfolio_id},action:SELL,qty:{random.randint(1, 50)}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes_payload)

        with patch('skills.market_portfolio_tax_rebalance_engine.open', create=True) as mock_open:
            mock_open.return_value = mock_stream

            execution_result = self.engine.execute_rebalance_from_stream(f"path/to/{uuid.uuid4()}.log")

            self.assertTrue(execution_result)
            mock_open.assert_called_once()

    def test_dividend_tax_offset_integration(self):
        portfolio_id = str(uuid.uuid4())
        ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        capital_gains = round(random.uniform(1000.0, 5000.0), 2)
        dividend_amount = round(random.uniform(200.0, 800.0), 2)

        self.tax_calculator.offset_dividends_against_gains.return_value = capital_gains - dividend_amount

        net_tax = self.engine.compute_net_tax_impact(portfolio_id, ticker, capital_gains, dividend_amount)

        self.assertIsInstance(net_tax, float)
        self.tax_calculator.offset_dividends_against_gains.assert_called_once_with(capital_gains, dividend_amount)

    def test_strategy_optimizer_fallback(self):
        portfolio_id = str(uuid.uuid4())
        self.strategy_optimizer.optimize.side_effect = Exception("Optimization Engine Failure")

        self.db_storage.get_portfolio.return_value = {
            'portfolio_id': portfolio_id,
            'assets': []
        }

        with self.assertRaises(TaxRebalanceException):
            self.engine.optimize_and_calculate_taxes(portfolio_id)

    def test_randomized_portfolio_tax_simulation(self):
        assets_count = random.randint(2, 5)
        portfolio = {
            'portfolio_id': str(uuid.uuid4()),
            'assets': [
                {
                    'ticker': ''.join(random.choices(string.ascii_uppercase, k=3)),
                    'shares': random.randint(10, 500),
                    'price': round(random.uniform(10.0, 1000.0), 2)
                } for _ in range(assets_count)
            ]
        }

        self.db_storage.get_portfolio.return_value = portfolio
        self.tax_calculator.simulate_tax_brackets.return_value = {"status": "optimized", "brackets": [0.13, 0.15]}

        simulation = self.engine.simulate_tax_brackets(portfolio['portfolio_id'])

        self.assertEqual(simulation['status'], "optimized")
        self.assertIn(0.13, simulation['brackets'])
        self.db_storage.get_portfolio.assert_called_with(portfolio['portfolio_id'])

if __name__ == '__main__':
    unittest.main()
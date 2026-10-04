import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.market_portfolio_deep_stress_analyzer import MarketPortfolioDeepStressAnalyzer

class TestMarketPortfolioDeepStressAnalyzer(unittest.TestCase):

    def setUp(self):
        self.db_storage = MagicMock()
        self.liquidity_analyzer = MagicMock()
        self.scenario_simulator = MagicMock()
        self.analyzer = MarketPortfolioDeepStressAnalyzer(
            db_storage=self.db_storage,
            market_portfolio_liquidity_scenario_analyzer=self.liquidity_analyzer,
            market_portfolio_scenario_simulator=self.scenario_simulator
        )

    def test_run_deep_stress_analysis_success(self):
        portfolio_id = str(uuid.uuid4())
        scenario_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        historical_window = random.randint(30, 365)

        expected_liquidity_data = {
            'depth_score': random.uniform(0.1, 1.0),
            'slippage_factor': random.uniform(0.01, 0.05)
        }
        expected_simulation_result = {
            'max_drawdown': random.uniform(-0.5, -0.1),
            'var_95': random.uniform(1000.0, 50000.0)
        }

        self.liquidity_analyzer.get_historical_liquidity.return_value = expected_liquidity_data
        self.scenario_simulator.run_simulation.return_value = expected_simulation_result

        result = self.analyzer.run_deep_stress_analysis(
            portfolio_id=portfolio_id,
            scenario_name=scenario_name,
            historical_window=historical_window
        )

        self.assertIn('analysis_id', result)
        self.assertEqual(result['portfolio_id'], portfolio_id)
        self.assertEqual(result['scenario_name'], scenario_name)
        self.assertEqual(result['liquidity_metrics'], expected_liquidity_data)
        self.assertEqual(result['simulation_results'], expected_simulation_result)
        self.db_storage.save_analysis.assert_called_once()

    def test_run_deep_stress_analysis_with_export(self):
        portfolio_id = str(uuid.uuid4())
        scenario_name = ''.join(random.choices(string.ascii_uppercase, k=10))
        export_format = random.choice(['json', 'csv', 'xml'])

        random_bytes = bytes(''.join(random.choices(string.printable, k=50)), 'utf-8')
        mock_exporter = MagicMock()
        mock_exporter.export.return_value = io.BytesIO(random_bytes)

        with patch('skills.market_portfolio_deep_stress_analyzer.market_portfolio_data_exporter', mock_exporter):
            result = self.analyzer.run_deep_stress_analysis_and_export(
                portfolio_id=portfolio_id,
                scenario_name=scenario_name,
                export_format=export_format
            )

        self.assertEqual(result['format'], export_format)
        self.assertIn(portfolio_id, result['metadata'])
        mock_exporter.export.assert_called_once()

    def test_evaluate_historical_volatility_impact(self):
        asset_ticker = ''.join(random.choices(string.ascii_uppercase, k=4))
        volatility_spike = random.uniform(1.5, 5.0)

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (str(uuid.uuid4()), random.uniform(100, 500), random.uniform(0.01, 0.05))
            for _ in range(5)
        ]
        self.db_storage.connection.cursor.return_value = mock_cursor

        impact = self.analyzer.evaluate_historical_volatility_impact(
            asset_ticker=asset_ticker,
            volatility_spike=volatility_spike
        )

        self.assertIn('ticker', impact)
        self.assertEqual(impact['ticker'], asset_ticker)
        self.assertIn('adjusted_var', impact)
        self.assertGreater(impact['adjusted_var'], 0.0)

    def test_aggregate_stress_signals(self):
        signal_id_1 = str(uuid.uuid4())
        signal_id_2 = str(uuid.uuid4())

        signals_input = [
            {'id': signal_id_1, 'severity': random.choice(['HIGH', 'CRITICAL'])},
            {'id': signal_id_2, 'severity': random.choice(['LOW', 'MEDIUM'])}
        ]

        aggregated = self.analyzer.aggregate_stress_signals(signals_input)

        self.assertEqual(len(aggregated['processed_signals']), 2)
        self.assertIn(signal_id_1, [s['id'] for s in aggregated['processed_signals']])
        self.assertIn(signal_id_2, [s['id'] for s in aggregated['processed_signals']])
        self.assertIn('aggregate_risk_score', aggregated)

if __name__ == '__main__':
    unittest.main()
import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
import io
from skills.market_portfolio_risk_engine import MarketPortfolioRiskEngine

class TestMarketPortfolioRiskEngine(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_aggregator = MagicMock()
        self.mock_simulator = MagicMock()
        self.engine = MarketPortfolioRiskEngine(
            db_storage=self.mock_db,
            market_portfolio_predictive_aggregator=self.mock_aggregator,
            market_portfolio_scenario_simulator=self.mock_simulator
        )

    def test_calculate_risk_metrics_integrity(self):
        portfolio_id = uuid.uuid4().hex
        volatility = random.uniform(0.01, 0.99)
        drawdown = random.uniform(-0.5, -0.01)

        expected_risk_score = (volatility * 0.7) + (abs(drawdown) * 0.3)

        with patch('skills.market_portfolio_risk_engine.MarketPortfolioRiskEngine._fetch_historical_data') as mock_fetch:
            mock_fetch.return_value = {'vol': volatility, 'dd': drawdown}

            result = self.engine.calculate_risk_metrics(portfolio_id)

            self.assertAlmostEqual(result['risk_score'], expected_risk_score, places=4)
            self.assertEqual(result['portfolio_id'], portfolio_id)

    def test_trigger_hedging_logic_on_anomaly(self):
        threshold = random.uniform(0.5, 0.8)
        high_risk_val = random.uniform(0.81, 1.0)
        portfolio_id = uuid.uuid4().hex

        with patch('skills.market_portfolio_risk_engine.MarketPortfolioRiskEngine.get_current_risk_level') as mock_risk:
            mock_risk.return_value = high_risk_val

            with patch('skills.market_portfolio_risk_engine.MarketPortfolioRiskEngine._execute_hedge_protocol') as mock_hedge:
                self.engine.evaluate_and_hedge(portfolio_id, threshold)

                mock_hedge.assert_called_once()
                args, _ = mock_hedge.call_args
                self.assertEqual(args[0], portfolio_id)

    def test_data_stream_processing(self):
        random_stream_id = uuid.uuid4().hex
        random_content = ''.join(random.choices(string.ascii_letters, k=64)).encode()

        with patch('skills.market_portfolio_risk_engine.MarketPortfolioRiskEngine._read_raw_stream') as mock_stream:
            mock_stream.return_value = io.BytesIO(random_content)

            processed_data = self.engine.process_raw_market_feed(random_stream_id)

            self.assertEqual(processed_data['source_id'], random_stream_id)
            self.assertEqual(processed_data['payload'], random_content)

    def test_audit_log_persistence(self):
        event_id = uuid.uuid4().hex
        risk_value = random.random()

        with patch('skills.market_portfolio_risk_engine.MarketPortfolioRiskEngine._write_to_audit') as mock_audit:
            self.engine.log_risk_event(event_id, risk_value)

            mock_audit.assert_called_once()
            call_args = mock_audit.call_args[0]
            self.assertIn(event_id, call_args)
            self.assertIn(risk_value, call_args)

    def test_insider_alert_integration(self):
        alert_id = uuid.uuid4().hex
        severity = random.choice(['LOW', 'MEDIUM', 'CRITICAL'])

        with patch('skills.market_portfolio_risk_engine.MarketPortfolioRiskEngine._dispatch_alert') as mock_dispatch:
            self.engine.handle_insider_signal(alert_id, severity)

            mock_dispatch.assert_called_once()
            self.assertEqual(mock_dispatch.call_args[0][0], alert_id)
            self.assertEqual(mock_dispatch.call_args[0][1], severity)

if __name__ == '__main__':
    unittest.main()
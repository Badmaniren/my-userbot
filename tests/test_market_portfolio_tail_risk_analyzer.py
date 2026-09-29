import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random

from skills.market_portfolio_tail_risk_analyzer import (
    TailRiskAnalyzer,
    MarketPortfolioTailRiskAnalyzer,
    market_portfolio_tail_risk_analyzer
)
from skills.db_storage import DBStorage


class TestMarketPortfolioTailRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = TailRiskAnalyzer()
        self.integration_analyzer = MarketPortfolioTailRiskAnalyzer()
        self.portfolio_id = uuid.uuid4().hex
        self.confidence_level = round(random.uniform(0.90, 0.99), 2)
        self.returns_data = [random.uniform(-0.1, 0.1) for _ in range(50)]

    def test_calculate_var(self):
        var_val = self.analyzer.calculate_var(self.returns_data, self.confidence_level)
        self.assertIsInstance(var_val, float)
        # Verify calculation
        sorted_data = sorted(self.returns_data)
        n = len(sorted_data)
        p = (1.0 - self.confidence_level) * 100.0
        k = (n - 1) * (p / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f
        expected_var = float(sorted_data[f] + d * (sorted_data[c] - sorted_data[f]))
        self.assertEqual(var_val, expected_var)

    def test_calculate_cvar(self):
        cvar_val = self.analyzer.calculate_cvar(self.returns_data, self.confidence_level)
        self.assertIsInstance(cvar_val, float)
        var = self.analyzer.calculate_var(self.returns_data, self.confidence_level)
        tail = [x for x in self.returns_data if x <= var]
        expected_cvar = float(sum(tail) / len(tail))
        self.assertEqual(cvar_val, expected_cvar)

    def test_compute_raw_metrics_and_calculate_tail_risk(self):
        res1 = self.analyzer.compute_raw_metrics(self.returns_data, self.confidence_level)
        res2 = self.analyzer.calculate_tail_risk(self.returns_data, self.confidence_level)
        self.assertIn('var', res1)
        self.assertIn('cvar', res1)
        self.assertEqual(res1, res2)

    def test_analyze_success(self):
        with patch('skills.market_portfolio_collector_agent.get_historical_returns') as mock_get_returns:
            mock_get_returns.return_value = self.returns_data
            result = self.analyzer.analyze(self.portfolio_id)
            self.assertIn('var', result)
            self.assertIn('cvar', result)
            self.assertIsInstance(result['var'], float)
            self.assertIsInstance(result['cvar'], float)
            mock_get_returns.assert_called_once_with(self.portfolio_id)

    def test_analyze_no_data(self):
        with patch('skills.market_portfolio_collector_agent.get_historical_returns') as mock_get_returns:
            mock_get_returns.return_value = []
            with self.assertRaises(ValueError):
                self.analyzer.analyze(self.portfolio_id)

            mock_get_returns.return_value = None
            with self.assertRaises(ValueError):
                self.analyzer.analyze(self.portfolio_id)

    def test_load_from_stream(self):
        random_floats = [random.uniform(-1.0, 1.0) for _ in range(10)]
        stream_content = ",".join(map(str, random_floats)).encode()
        mock_file_path = uuid.uuid4().hex + ".txt"

        fake_file = io.BytesIO(stream_content)
        with patch('builtins.open', return_value=fake_file) as mock_open:
            result = self.analyzer.load_from_stream(mock_file_path)
            self.assertIsInstance(result, list)
            mock_open.assert_called_once_with(mock_file_path, 'rb')

    def test_check_risk_status(self):
        expected_status = {uuid.uuid4().hex: random.random()}
        with patch('skills.market_anomaly_detector.check_portfolio', return_value=expected_status) as mock_check:
            status = self.analyzer.check_risk_status(self.portfolio_id)
            self.assertEqual(status, expected_status)
            mock_check.assert_called_once_with(self.portfolio_id)

    def test_market_portfolio_tail_risk_analyzer_init(self):
        mock_db = MagicMock(spec=DBStorage)
        analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=mock_db)
        self.assertEqual(analyzer.db, mock_db)

    def test_calculate_risk_metrics_success(self):
        mock_db = MagicMock(spec=DBStorage)
        mock_returns_list = list(self.returns_data)
        mock_db.get_portfolio_history.return_value = mock_returns_list

        analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=mock_db)
        result = analyzer.calculate_risk_metrics(self.portfolio_id, self.confidence_level)

        self.assertIn('var', result)
        self.assertIn('cvar', result)
        mock_db.get_portfolio_history.assert_called_once_with(self.portfolio_id)
        mock_db.save_report.assert_called_once()

    def test_calculate_risk_metrics_not_found(self):
        mock_db = MagicMock(spec=DBStorage)
        mock_db.get_portfolio_history.return_value = []

        analyzer = MarketPortfolioTailRiskAnalyzer(db_storage=mock_db)
        with self.assertRaises(ValueError):
            analyzer.calculate_risk_metrics(self.portfolio_id, self.confidence_level)
        mock_db.get_portfolio_history.assert_called_once_with(self.portfolio_id)

    def test_top_level_entry_point(self):
        res1 = market_portfolio_tail_risk_analyzer(returns=self.returns_data, confidence_level=0.95)
        self.assertIn('var', res1)
        self.assertIn('cvar', res1)


if __name__ == '__main__':
    unittest.main()

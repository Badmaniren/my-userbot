import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from skills.market_portfolio_liquidity_analyzer import (
    calculate_adv,
    estimate_liquidation_time,
    score_liquidity_risk,
    MarketPortfolioLiquidityAnalyzer
)

class TestMarketPortfolioLiquidityAnalyzer(unittest.TestCase):

    def setUp(self):
        self.random_portfolio_id = str(uuid.uuid4())
        self.random_ticker = ''.join(random.choices(string.ascii_uppercase, k=5))
        self.random_volumes = [random.randint(1000, 1000000) for _ in range(10)]
        self.random_position_size = random.randint(10000, 5000000)
        self.random_adv = random.randint(50000, 1000000)

    def test_calculate_adv_valid(self):
        expected_adv = sum(self.random_volumes) / len(self.random_volumes)
        result = calculate_adv(self.random_volumes)
        self.assertAlmostEqual(result, expected_adv, places=2)

    def test_calculate_adv_empty_raises(self):
        with self.assertRaises(ValueError):
            calculate_adv([])

    def test_estimate_liquidation_time_valid(self):
        participation_rate = round(random.uniform(0.05, 0.3), 2)
        expected_days = self.random_position_size / (self.random_adv * participation_rate)
        result = estimate_liquidation_time(self.random_position_size, self.random_adv, participation_rate)
        self.assertAlmostEqual(result, expected_days, places=2)

    def test_estimate_liquidation_time_zero_adv(self):
        with self.assertRaises(ZeroDivisionError):
            estimate_liquidation_time(self.random_position_size, 0.0)

    def test_score_liquidity_risk_levels(self):
        days_low = round(random.uniform(0.1, 1.0), 2)
        days_med = round(random.uniform(2.0, 5.0), 2)
        days_high = round(random.uniform(6.0, 30.0), 2)

        self.assertEqual(score_liquidity_risk(days_low), "LOW")
        self.assertEqual(score_liquidity_risk(days_med), "MEDIUM")
        self.assertEqual(score_liquidity_risk(days_high), "HIGH")

    def test_analyzer_class_workflow(self):
        mock_db_storage = MagicMock()
        mock_extractor = MagicMock()

        raw_stream_data = f"ticker:{self.random_ticker},vol:{','.join(map(str, self.random_volumes))}".encode('utf-8')
        mock_stream = io.BytesIO(raw_stream_data)

        with patch('skills.market_portfolio_liquidity_analyzer.market_parser') as mock_parser:
            mock_parser.parse_stream.return_value = {
                'ticker': self.random_ticker,
                'volumes': self.random_volumes,
                'position_size': self.random_position_size
            }

            analyzer = MarketPortfolioLiquidityAnalyzer(
                db_storage=mock_db_storage,
                extractor_tool=mock_extractor
            )

            analysis_result = analyzer.analyze_stream(mock_stream, portfolio_id=self.random_portfolio_id)

            self.assertIn('ticker', analysis_result)
            self.assertEqual(analysis_result['ticker'], self.random_ticker)
            self.assertIn('adv', analysis_result)
            self.assertIn('liquidation_days', analysis_result)
            self.assertIn('risk_score', analysis_result)
            self.assertIn(analysis_result['risk_score'], ["LOW", "MEDIUM", "HIGH"])

            mock_db_storage.save_liquidity_metric.assert_called_once()

    def test_analyzer_with_anomaly_detection(self):
        mock_anomaly_detector = MagicMock()
        mock_anomaly_detector.check_anomaly.return_value = True

        analyzer = MarketPortfolioLiquidityAnalyzer(
            db_storage=MagicMock(),
            market_anomaly_detector=mock_anomaly_detector
        )

        with patch.object(analyzer, '_fetch_historical_volumes') as mock_fetch:
            mock_fetch.return_value = self.random_volumes

            report = analyzer.evaluate_position_liquidity(
                ticker=self.random_ticker,
                position_size=self.random_position_size
            )

            self.assertTrue(report['anomaly_flag'])
            mock_anomaly_detector.check_anomaly.assert_called_once()
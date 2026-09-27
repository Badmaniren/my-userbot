import unittest
from unittest.mock import patch, MagicMock
import io
import csv
import uuid
import random
from datetime import datetime, timedelta

from skills.market_portfolio_drawdown_analyzer import (
    calculate_max_drawdown,
    calculate_calmar_ratio,
    analyze_recovery_profile,
    store_drawdown_metrics,
    MarketPortfolioDrawdownAnalyzer
)


class TestMarketPortfolioDrawdownAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarketPortfolioDrawdownAnalyzer()
        self.rand_str = uuid.uuid4().hex[:8]

    def test_calculate_max_drawdown_empty_and_edge(self):
        res1 = self.analyzer.calculate_max_drawdown([])
        self.assertEqual(res1["max_drawdown"], 0.0)
        self.assertEqual(res1["duration"], 0)

        res2 = self.analyzer.calculate_max_drawdown(None)
        self.assertEqual(res2["max_drawdown"], 0.0)
        self.assertEqual(res2["duration"], 0)

        res3 = self.analyzer.calculate_max_drawdown([{"value": None}, {"portfolio_value": None}])
        self.assertEqual(res3["max_drawdown"], 0.0)

    def test_calculate_max_drawdown_functional(self):
        peak = round(random.uniform(1000.0, 5000.0), 2)
        trough = round(peak * random.uniform(0.3, 0.8), 2)
        recovery = round(peak * random.uniform(0.9, 1.2), 2)

        data = [
            {"portfolio_value": peak},
            {"portfolio_value": trough},
            {"portfolio_value": recovery}
        ]

        expected_dd = (peak - trough) / peak
        result = self.analyzer.calculate_max_drawdown(data)

        self.assertAlmostEqual(result["max_drawdown"], expected_dd, places=4)
        self.assertGreaterEqual(result["duration"], 0)

    def test_calculate_calmar_ratio(self):
        ret = round(random.uniform(0.05, 0.5), 4)
        dd = -round(random.uniform(0.1, 0.4), 4)

        calmar = self.analyzer.calculate_calmar_ratio(ret, dd)
        self.assertAlmostEqual(calmar, ret / abs(dd), places=4)

        zero_calmar = self.analyzer.calculate_calmar_ratio(ret, 0.0)
        self.assertEqual(zero_calmar, 0.0)

    def test_generate_recovery_profile(self):
        series_len = random.randint(5, 20)
        series = [round(random.uniform(100.0, 1000.0), 2) for _ in range(series_len)]
        profile = self.analyzer.generate_recovery_profile(series)

        self.assertIn("recovery_periods", profile)
        self.assertIn("fully_recovered", profile)
        self.assertIsInstance(profile["recovery_periods"], int)
        self.assertIsInstance(profile["fully_recovered"], bool)

    def test_analyze_from_storage_mocked(self):
        mock_history = [
            round(random.uniform(2000.0, 3000.0), 2),
            round(random.uniform(1000.0, 1999.0), 2),
            round(random.uniform(2500.0, 3500.0), 2)
        ]

        with patch("skills.market_portfolio_drawdown_analyzer.db_storage") as mock_db:
            mock_db.get_portfolio_history.return_value = mock_history
            db_key = f"portfolio_{uuid.uuid4().hex}"
            res = self.analyzer.analyze_from_storage(db_key)

            mock_db.get_portfolio_history.assert_called_once_with(db_key)
            self.assertIn("max_drawdown", res)
            self.assertGreater(res["max_drawdown"], 0.0)

    def test_parse_and_analyze_stream(self):
        val1 = round(random.uniform(500.0, 1000.0), 2)
        val2 = round(random.uniform(100.0, 499.0), 2)
        val3 = round(random.uniform(600.0, 1200.0), 2)

        csv_content = f"2023-01-01,{val1}\n2023-01-02,{val2}\n2023-01-03,{val3}\n"
        stream = io.BytesIO(csv_content.encode('utf-8'))

        res = self.analyzer.parse_and_analyze_stream(stream)
        self.assertIn("max_drawdown", res)
        self.assertGreaterEqual(res["max_drawdown"], 0.0)


class TestMarketPortfolioDrawdownAnalyzerIntegration(unittest.TestCase):

    def test_functional_helpers(self):
        val1 = round(random.uniform(10000.0, 20000.0), 2)
        val2 = round(random.uniform(5000.0, 9999.0), 2)

        ts1 = datetime.now().isoformat()
        ts2 = (datetime.now() + timedelta(days=random.randint(1, 10))).isoformat()

        data = [
            {"value": val1, "timestamp": ts1},
            {"value": val2, "timestamp": ts2}
        ]

        max_dd, peak_date, trough_date = calculate_max_drawdown(data)
        self.assertLess(max_dd, 0.0)
        self.assertEqual(peak_date, ts1)
        self.assertEqual(trough_date, ts2)

        ret = round(random.uniform(0.1, 0.3), 2)
        calmar = calculate_calmar_ratio(ret, max_dd)
        self.assertAlmostEqual(calmar, ret / abs(max_dd))

        recovery = analyze_recovery_profile(data, peak_date, trough_date)
        self.assertIn("recovery_duration_days", recovery)
        self.assertGreaterEqual(recovery["recovery_duration_days"], 0)

    def test_store_drawdown_metrics(self):
        metric_record = {
            "metric_id": uuid.uuid4().hex,
            "max_drawdown": round(random.uniform(0.01, 0.5), 4),
            "calmar_ratio": round(random.uniform(0.1, 5.0), 4),
            "timestamp": datetime.now().isoformat()
        }

        with patch("skills.market_portfolio_drawdown_analyzer.save_to_db") as mock_save, \
             patch("skills.market_portfolio_drawdown_analyzer.db_storage") as mock_db:

            mock_db.save_to_db = MagicMock()
            success = store_drawdown_metrics(metric_record)

            self.assertTrue(success)
            mock_save.assert_called_once_with(metric_record)
            mock_db.save_to_db.assert_called_once_with(metric_record)

    def test_module_level_empty_cases(self):
        self.assertEqual(calculate_max_drawdown([]), (0.0, None, None))
        self.assertEqual(calculate_max_drawdown(None), (0.0, None, None))
        self.assertEqual(calculate_calmar_ratio(0.2, 0.0), 0.0)

        profile = analyze_recovery_profile([], None, None)
        self.assertEqual(profile["recovery_duration_days"], 5)
        self.assertTrue(profile["fully_recovered"])
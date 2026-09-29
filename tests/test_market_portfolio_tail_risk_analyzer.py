import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import sys

try:
    import numpy
except ImportError:
    class MockNumpyArray:
        def __init__(self, data, dtype=float):
            self.data = [float(x) for x in data]
        def __le__(self, other):
            return [x <= other for x in self.data]
        def __getitem__(self, item):
            if isinstance(item, list):
                return MockNumpyArray([self.data[i] for i, val in enumerate(item) if val])
            return self.data[item]
        def __len__(self):
            return len(self.data)

    class MockNumpy:
        def array(self, data, dtype=float):
            return MockNumpyArray(data, dtype)
        def percentile(self, arr, q):
            sorted_data = sorted(arr.data if isinstance(arr, MockNumpyArray) else arr)
            k = (len(sorted_data) - 1) * (q / 100.0)
            f = int(k)
            c = f + 1
            if c < len(sorted_data):
                return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)
            return sorted_data[min(f, len(sorted_data) - 1)]
        def sqrt(self, val):
            return val ** 0.5
        def mean(self, arr):
            data = arr.data if isinstance(arr, MockNumpyArray) else arr
            return sum(data) / len(data) if data else 0.0
        class random:
            @staticmethod
            def normal(loc, scale, size):
                return [loc + scale * random.gauss(0, 1) for _ in range(size)]

    sys.modules['numpy'] = MockNumpy()

from skills.market_portfolio_tail_risk_analyzer import (
    MarketPortfolioTailRiskAnalyzer,
    market_portfolio_tail_risk_analyzer
)

class TestMarketPortfolioTailRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = MarketPortfolioTailRiskAnalyzer()
        self.portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        self.returns = [random.uniform(-0.05, 0.05) for _ in range(50)]
        self.confidence = random.choice([0.90, 0.95, 0.99])
        self.horizon = random.randint(1, 10)
        self.threshold = random.uniform(0.01, 0.1)

    def test_compute_var_success(self):
        res = self.analyzer.compute_var(self.portfolio_id, self.returns, self.confidence, self.horizon)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertIn("var_value", res)
        self.assertGreaterEqual(res["var_value"], 0.0)
        self.assertEqual(res["confidence"], self.confidence)
        self.assertEqual(res["horizon"], self.horizon)

    def test_compute_var_empty_returns_raises(self):
        with self.assertRaises(ZeroDivisionError):
            self.analyzer.compute_var(self.portfolio_id, [], self.confidence, self.horizon)

    def test_compute_cvar_success(self):
        cvar = self.analyzer.compute_cvar(self.portfolio_id, self.returns, self.confidence)
        self.assertIsInstance(cvar, float)
        self.assertGreaterEqual(cvar, 0.0)

    def test_compute_cvar_empty_returns_raises(self):
        with self.assertRaises(ZeroDivisionError):
            self.analyzer.compute_cvar(self.portfolio_id, [], self.confidence)

    def test_compute_cvar_with_anomaly_detector(self):
        mock_detector = MagicMock()
        with patch("skills.market_portfolio_tail_risk_analyzer.market_anomaly_detector", mock_detector):
            cvar = self.analyzer.compute_cvar(self.portfolio_id, self.returns, self.confidence)
            mock_detector.analyze.assert_called_once_with(self.returns)
            self.assertIsInstance(cvar, float)

    def test_run_tail_risk_stress_test_default(self):
        scenario = f"scenario_{uuid.uuid4().hex[:6]}"
        shock = random.uniform(-0.5, -0.1)
        res = self.analyzer.run_tail_risk_stress_test(self.portfolio_id, scenario, shock)
        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["scenario"], scenario)
        self.assertEqual(res["shock"], shock)
        self.assertEqual(res["status"], "COMPLETED")

    def test_run_tail_risk_stress_test_pipeline(self):
        scenario = f"scenario_{uuid.uuid4().hex[:6]}"
        shock = random.uniform(-0.5, -0.1)
        expected_output = {"portfolio_id": self.portfolio_id, "status": "PIPELINE_OK", "scenario": scenario}

        mock_pipeline = MagicMock()
        mock_pipeline.run_stress_test.return_value = expected_output

        with patch("skills.market_portfolio_tail_risk_analyzer.market_portfolio_stress_scenario_pipeline", mock_pipeline):
            res = self.analyzer.run_tail_risk_stress_test(self.portfolio_id, scenario, shock)
            mock_pipeline.run_stress_test.assert_called_once_with(
                portfolio_id=self.portfolio_id, scenario=scenario, shock=shock
            )
            self.assertEqual(res, expected_output)

    def test_check_and_dispatch_risk_alert_triggered(self):
        current_var = self.threshold + random.uniform(0.01, 0.05)
        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = True

        with patch("skills.market_portfolio_tail_risk_analyzer.market_portfolio_alert_dispatcher", mock_dispatcher):
            dispatched = self.analyzer.check_and_dispatch_risk_alert(self.portfolio_id, current_var, self.threshold)
            self.assertTrue(dispatched)
            mock_dispatcher.dispatch.assert_called_once_with(
                portfolio_id=self.portfolio_id, var=current_var, threshold=self.threshold
            )

    def test_check_and_dispatch_risk_alert_not_triggered(self):
        current_var = self.threshold - random.uniform(0.001, 0.01)
        dispatched = self.analyzer.check_and_dispatch_risk_alert(self.portfolio_id, current_var, self.threshold)
        self.assertFalse(dispatched)

    def test_analyze_portfolio_full(self):
        config = {
            "portfolio_id": self.portfolio_id,
            "confidence_level": self.confidence,
            "horizon_days": self.horizon,
            "simulation_runs": 500
        }

        mock_valuation = {"value": random.uniform(10000, 500000), "currency": "USD"}
        mock_db = MagicMock()

        with patch("skills.market_portfolio_tail_risk_analyzer.market_portfolio_valuation") as val_mock, \
             patch("skills.market_portfolio_tail_risk_analyzer.db_storage", mock_db):

            val_mock.calculate_current_value.return_value = mock_valuation

            report = self.analyzer.analyze_portfolio(config)

            self.assertEqual(report["portfolio_id"], self.portfolio_id)
            self.assertIn("var", report)
            self.assertIn("cvar", report)
            self.assertEqual(report["confidence"], self.confidence)
            self.assertEqual(report["horizon_days"], self.horizon)
            self.assertEqual(report["valuation"], mock_valuation)
            self.assertIn("timestamp", report)

            mock_db.persist_state.assert_called_once()
            args = mock_db.persist_state.call_args[0]
            self.assertTrue(args[0].startswith("risk_report_"))

    def test_procedural_wrapper(self):
        config = {"portfolio_id": self.portfolio_id, "confidence_level": self.confidence}
        mock_valuation = {"value": 12345.67}
        mock_db = MagicMock()

        with patch("skills.market_portfolio_tail_risk_analyzer.market_portfolio_valuation") as val_mock, \
             patch("skills.market_portfolio_tail_risk_analyzer.db_storage", mock_db):

            val_mock.calculate_current_value.return_value = mock_valuation
            res = market_portfolio_tail_risk_analyzer(config)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)

    def test_procedural_wrapper_string_fallback(self):
        mock_valuation = {"value": 98765.43}
        mock_db = MagicMock()

        with patch("skills.market_portfolio_tail_risk_analyzer.market_portfolio_valuation") as val_mock, \
             patch("skills.market_portfolio_tail_risk_analyzer.db_storage", mock_db):

            val_mock.calculate_current_value.return_value = mock_valuation
            res = market_portfolio_tail_risk_analyzer(self.portfolio_id)
            self.assertEqual(res["portfolio_id"], self.portfolio_id)
import unittest
from unittest.mock import MagicMock
import uuid

from skills.market_anomaly_score_calculator import (
    MarketAnomalyScoreCalculator,
    AnomalyScoreCalculator,
    calculate_market_anomaly_score,
    evaluate_insider_event_probability,
    process_anomaly_score_stream
)


class TestMarketAnomalyScoreCalculator(unittest.TestCase):

    def setUp(self):
        self.calculator = MarketAnomalyScoreCalculator()

    def test_alias_class(self):
        self.assertEqual(MarketAnomalyScoreCalculator, AnomalyScoreCalculator)

    def test_calculate_z_score_valid(self):
        data_history = [10.0, 12.0, 14.0, 16.0, 18.0]
        z_score = self.calculator.calculate_z_score(20.0, data_history)
        self.assertIsInstance(z_score, float)
        self.assertGreater(z_score, 0)

    def test_calculate_z_score_edge_cases(self):
        self.assertEqual(self.calculator.calculate_z_score(None, [1, 2, 3]), 0.0)
        self.assertEqual(self.calculator.calculate_z_score(10, []), 0.0)
        self.assertEqual(self.calculator.calculate_z_score(10, [5]), 0.0)
        self.assertEqual(self.calculator.calculate_z_score(10, [5, 5, 5]), 0.0)

    def test_calculate_volume_price_volatility_scores(self):
        history = [100.0, 100.0, 100.0, 100.0, 200.0]
        v_score = self.calculator.calculate_volume_score(300.0, history)
        p_score = self.calculator.calculate_price_score(300.0, history)
        vol_score = self.calculator.calculate_volatility_score(300.0, history)

        self.assertGreater(v_score, 0)
        self.assertGreater(p_score, 0)
        self.assertGreater(vol_score, 0)

    def test_calculate_anomaly_score(self):
        score_res = self.calculator.calculate_anomaly_score(
            volume_z=2.5,
            price_z=1.8,
            volatility_z=2.0
        )
        self.assertIn("composite_score", score_res)
        self.assertIn("insider_event_probability", score_res)
        self.assertIn("is_anomaly", score_res)
        self.assertIn("severity", score_res)

        self.assertGreaterEqual(score_res["insider_event_probability"], 0.0)
        self.assertLessEqual(score_res["insider_event_probability"], 1.0)
        self.assertTrue(score_res["is_anomaly"])

    def test_evaluate_insider_probability(self):
        prob = self.calculator.evaluate_insider_probability(3.0, 2.5, 2.0)
        self.assertIsInstance(prob, float)
        self.assertGreaterEqual(prob, 0.5)

    def test_evaluate_market_data_with_mocks(self):
        mock_db = MagicMock()
        mock_alert = MagicMock()
        calc = MarketAnomalyScoreCalculator(db_storage=mock_db, alert_dispatcher=mock_alert)

        symbol = f"BTC_{uuid.uuid4().hex[:6]}"
        data = {
            "volume_z": 3.0,
            "price_z": 2.5,
            "volatility_z": 2.0
        }

        res = calc.evaluate_market_data(symbol, data=data)
        self.assertEqual(res["symbol"], symbol)
        self.assertTrue(res["is_anomaly"])

        mock_db.save.assert_called_once()
        mock_alert.dispatch.assert_called_once()

    def test_top_level_helper_functions(self):
        top_res = calculate_market_anomaly_score(
            volume_z=2.0,
            price_z=1.5,
            volatility_z=1.0
        )
        self.assertIn("insider_event_probability", top_res)

        prob = evaluate_insider_event_probability(2.5, 2.0, 1.5)
        self.assertIsInstance(prob, float)

        stream_res = process_anomaly_score_stream({"symbol": "ETH", "volume_z": 1.0, "price_z": 0.5, "volatility_z": 0.5})
        self.assertEqual(stream_res["symbol"], "ETH")


if __name__ == "__main__":
    unittest.main()

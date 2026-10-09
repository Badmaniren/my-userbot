import unittest
from unittest.mock import patch
import uuid
import random
import io

from skills.market_portfolio_stress_ml_volatility_forecaster import market_portfolio_stress_ml_volatility_forecaster

class TestMarketPortfolioStressMLVolatilityForecaster(unittest.TestCase):

    def test_ml_volatility_forecaster_success(self):
        p_id = uuid.uuid4().hex
        rnd_threshold = round(random.uniform(0.01, 0.5), 4)
        rnd_vol = round(random.uniform(0.1, 0.9), 4)

        mock_db_data = {"base_volatility": rnd_vol}

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.extractor_tool_1790087207') as mock_extractor, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.market_anomaly_detector') as mock_anomaly, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.market_portfolio_alert_dispatcher') as mock_dispatcher:

            mock_db.side_effect = lambda action, key: mock_db_data if action == "get" else None
            mock_extractor.get_metrics.return_value = [uuid.uuid4().hex, uuid.uuid4().hex]
            mock_anomaly.check_anomaly.return_value = False

            result = market_portfolio_stress_ml_volatility_forecaster(
                portfolio_id=p_id,
                threshold=rnd_threshold
            )

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("portfolio_id"), p_id)
            self.assertEqual(result.get("status"), "success")
            self.assertIn("volatility_forecast", result)
            expected_vol = rnd_vol * (1.0 + rnd_threshold)
            self.assertAlmostEqual(result.get("volatility_forecast"), expected_vol)
            self.assertIsInstance(result.get("metrics"), list)

    def test_ml_volatility_forecaster_with_monte_carlo(self):
        p_id = uuid.uuid4().hex
        rnd_monte_vol = round(random.uniform(0.2, 0.8), 4)
        monte_output = {"volatility": rnd_monte_vol}

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.extractor_tool_1790087207') as mock_extractor, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.market_anomaly_detector') as mock_anomaly:

            mock_db.return_value = None
            mock_extractor.get_metrics.return_value = []
            mock_anomaly.check_anomaly.return_value = True

            result = market_portfolio_stress_ml_volatility_forecaster(
                portfolio_id=p_id,
                monte_carlo_output=monte_output
            )

            self.assertEqual(result.get("portfolio_id"), p_id)
            expected_vol = rnd_monte_vol * 1.25
            self.assertAlmostEqual(result.get("volatility_forecast"), expected_vol)

    def test_ml_volatility_forecaster_with_stream_io(self):
        p_id = uuid.uuid4().hex
        stream_content = uuid.uuid4().bytes
        stream_obj = io.BytesIO(stream_content)

        with patch('skills.market_portfolio_stress_ml_volatility_forecaster.db_storage') as mock_db, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.market_parser') as mock_parser, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.extractor_tool_1790087207') as mock_extractor, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.market_anomaly_detector') as mock_anomaly, \
             patch('skills.market_portfolio_stress_ml_volatility_forecaster.market_portfolio_alert_dispatcher') as mock_dispatcher:

            mock_db.return_value = None
            mock_extractor.get_metrics.return_value = [uuid.uuid4().hex]
            mock_anomaly.check_anomaly.return_value = True

            result = market_portfolio_stress_ml_volatility_forecaster(
                portfolio_id=p_id,
                stream_data=stream_obj,
                threshold=0.1
            )

            mock_parser.parse_stream.assert_called_once_with(stream_obj)
            mock_dispatcher.dispatch.assert_called_once_with(p_id)
            self.assertEqual(result.get("status"), "success")

if __name__ == '__main__':
    unittest.main()
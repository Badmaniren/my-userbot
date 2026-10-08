import unittest
from unittest.mock import MagicMock, patch
import random
import uuid
import string
import io

from skills.market_insider_hedging_calculator import MarketInsiderHedgingCalculator


class TestMarketInsiderHedgingCalculator(unittest.TestCase):

    def setUp(self):
        self.mock_db_storage = MagicMock()
        self.mock_anomaly_analyzer = MagicMock()
        self.mock_portfolio_valuation = MagicMock()

        self.calculator = MarketInsiderHedgingCalculator(
            db_storage=self.mock_db_storage,
            anomaly_analyzer=self.mock_anomaly_analyzer,
            portfolio_valuation=self.mock_portfolio_valuation
        )

    def _generate_random_string(self, length=12):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def _generate_random_asset(self):
        return "".join(random.choices(string.ascii_uppercase, k=random.randint(3, 5)))

    def test_calculate_hedging_parameters_success(self):
        portfolio_id = f"port-{uuid.uuid4().hex}"
        anomaly_id = f"anom-{uuid.uuid4().hex}"
        asset_symbol = self._generate_random_asset()

        portfolio_value = random.uniform(500000.0, 10000000.0)
        asset_exposure = random.uniform(50000.0, portfolio_value * 0.4)
        anomaly_score = random.uniform(0.6, 0.99)
        risk_tolerance = random.uniform(0.1, 0.5)

        self.mock_portfolio_valuation.get_portfolio_exposure.return_value = {
            "total_value": portfolio_value,
            "asset_exposure": asset_exposure,
            "asset": asset_symbol
        }

        self.mock_anomaly_analyzer.get_anomaly_details.return_value = {
            "anomaly_id": anomaly_id,
            "asset": asset_symbol,
            "anomaly_score": anomaly_score,
            "direction": "SHORT",
            "confidence": random.uniform(0.7, 0.95)
        }

        result = self.calculator.calculate_hedging_parameters(
            portfolio_id=portfolio_id,
            anomaly_id=anomaly_id,
            risk_tolerance=risk_tolerance
        )

        expected_hedging_volume = asset_exposure * anomaly_score * (1.0 - risk_tolerance)

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertEqual(result["anomaly_id"], anomaly_id)
        self.assertEqual(result["asset"], asset_symbol)
        self.assertAlmostEqual(result["hedging_volume"], expected_hedging_volume, places=4)
        self.assertTrue(result["hedging_volume"] > 0)

        self.mock_db_storage.save_hedging_strategy.assert_called_once()
        saved_args = self.mock_db_storage.save_hedging_strategy.call_args[0][0]
        self.assertEqual(saved_args["portfolio_id"], portfolio_id)
        self.assertAlmostEqual(saved_args["hedging_volume"], expected_hedging_volume, places=4)

    def test_calculate_hedging_parameters_zero_exposure(self):
        portfolio_id = f"port-{uuid.uuid4().hex}"
        anomaly_id = f"anom-{uuid.uuid4().hex}"
        asset_symbol = self._generate_random_asset()

        portfolio_value = random.uniform(100000.0, 1000000.0)
        asset_exposure = 0.0
        anomaly_score = random.uniform(0.5, 0.95)
        risk_tolerance = random.uniform(0.1, 0.8)

        self.mock_portfolio_valuation.get_portfolio_exposure.return_value = {
            "total_value": portfolio_value,
            "asset_exposure": asset_exposure,
            "asset": asset_symbol
        }

        self.mock_anomaly_analyzer.get_anomaly_details.return_value = {
            "anomaly_id": anomaly_id,
            "asset": asset_symbol,
            "anomaly_score": anomaly_score,
            "direction": "SHORT",
            "confidence": random.uniform(0.5, 0.9)
        }

        result = self.calculator.calculate_hedging_parameters(
            portfolio_id=portfolio_id,
            anomaly_id=anomaly_id,
            risk_tolerance=risk_tolerance
        )

        self.assertEqual(result["hedging_volume"], 0.0)
        self.assertEqual(result["status"], "NO_HEDGING_REQUIRED")

    def test_calculate_hedging_parameters_invalid_risk_tolerance(self):
        portfolio_id = f"port-{uuid.uuid4().hex}"
        anomaly_id = f"anom-{uuid.uuid4().hex}"
        invalid_risk_tolerance = random.choice([-random.uniform(0.1, 5.0), random.uniform(1.01, 10.0)])

        with self.assertRaises(ValueError):
            self.calculator.calculate_hedging_parameters(
                portfolio_id=portfolio_id,
                anomaly_id=anomaly_id,
                risk_tolerance=invalid_risk_tolerance
            )

    def test_calculate_hedging_parameters_missing_anomaly(self):
        portfolio_id = f"port-{uuid.uuid4().hex}"
        anomaly_id = f"anom-{uuid.uuid4().hex}"
        risk_tolerance = random.uniform(0.1, 0.9)

        self.mock_anomaly_analyzer.get_anomaly_details.return_value = None

        with self.assertRaises(KeyError):
            self.calculator.calculate_hedging_parameters(
                portfolio_id=portfolio_id,
                anomaly_id=anomaly_id,
                risk_tolerance=risk_tolerance
            )

    def test_load_config_from_stream(self):
        random_multiplier = random.uniform(1.05, 2.95)
        random_threshold = random.uniform(0.01, 0.09)
        config_json = f'{{"multiplier": {random_multiplier}, "min_threshold": {random_threshold}}}'

        stream = io.BytesIO(config_json.encode('utf-8'))

        self.calculator.load_config_from_stream(stream)

        self.assertAlmostEqual(self.calculator.multiplier, random_multiplier, places=4)
        self.assertAlmostEqual(self.calculator.min_threshold, random_threshold, places=4)

    def test_export_report_to_stream(self):
        portfolio_id = f"port-{uuid.uuid4().hex}"
        anomaly_id = f"anom-{uuid.uuid4().hex}"
        asset_symbol = self._generate_random_asset()
        hedging_volume = random.uniform(1000.0, 50000.0)

        report_data = {
            "portfolio_id": portfolio_id,
            "anomaly_id": anomaly_id,
            "asset": asset_symbol,
            "hedging_volume": hedging_volume
        }

        stream = io.BytesIO()
        self.calculator.export_report_to_stream(stream, report_data)

        stream.seek(0)
        written_content = stream.read().decode('utf-8')

        self.assertIn(portfolio_id, written_content)
        self.assertIn(anomaly_id, written_content)
        self.assertIn(asset_symbol, written_content)
        self.assertIn(f"{hedging_volume:.2f}", written_content)

    def test_external_api_integration_with_patch(self):
        portfolio_id = f"port-{uuid.uuid4().hex}"
        anomaly_id = f"anom-{uuid.uuid4().hex}"
        asset_symbol = self._generate_random_asset()

        portfolio_value = random.uniform(100000.0, 500000.0)
        asset_exposure = random.uniform(10000.0, 50000.0)
        anomaly_score = random.uniform(0.5, 0.9)
        risk_tolerance = random.uniform(0.2, 0.4)

        self.mock_portfolio_valuation.get_portfolio_exposure.return_value = {
            "total_value": portfolio_value,
            "asset_exposure": asset_exposure,
            "asset": asset_symbol
        }

        self.mock_anomaly_analyzer.get_anomaly_details.return_value = {
            "anomaly_id": anomaly_id,
            "asset": asset_symbol,
            "anomaly_score": anomaly_score,
            "direction": "SHORT",
            "confidence": random.uniform(0.5, 0.9)
        }

        random_api_response = {
            "status": "success",
            "transaction_id": f"tx-{uuid.uuid4().hex}"
        }

        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = random_api_response

            result = self.calculator.calculate_and_execute_hedging(
                portfolio_id=portfolio_id,
                anomaly_id=anomaly_id,
                risk_tolerance=risk_tolerance,
                execution_endpoint=f"https://api.{self._generate_random_string(5)}.com/execute"
            )

            self.assertEqual(result["execution_status"], "success")
            self.assertEqual(result["transaction_id"], random_api_response["transaction_id"])
            mock_post.assert_called_once()


if __name__ == "__main__":
    unittest.main()
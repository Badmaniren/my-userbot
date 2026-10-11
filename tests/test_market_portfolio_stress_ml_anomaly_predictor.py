import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
from skills.market_portfolio_stress_ml_anomaly_predictor import start_new, market_portfolio_stress_ml_anomaly_predictor


class TestMarketPortfolioStressMlAnomalyPredictor(unittest.TestCase):

    def test_start_new_anomaly_detected_explicit(self):
        portfolio_id = str(uuid.uuid4())
        connection_string = f"postgresql://user_{uuid.uuid4().hex[:6]}:pass@{uuid.uuid4().hex[:6]}:5432/db_{uuid.uuid4().hex[:6]}"
        threshold = round(random.uniform(0.1, 0.9), 2)
        risk_score = round(threshold + random.uniform(0.01, 0.2), 2)
        confidence = round(random.uniform(0.5, 0.99), 2)

        def mock_detector(**kwargs):
            return {
                "anomaly_detected": True,
                "risk_score": risk_score,
                "confidence": confidence
            }

        mock_db = MagicMock()
        mock_extractor = MagicMock(return_value=io.BytesIO(uuid.uuid4().bytes))

        result = start_new(
            portfolio_id=portfolio_id,
            connection_string=connection_string,
            threshold=threshold,
            extractor_tool_1790087207=mock_extractor,
            market_anomaly_detector=mock_detector,
            db_storage=mock_db
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["risk_score"], risk_score)
        self.assertEqual(result["confidence"], confidence)
        mock_db.save.assert_called_once()
        saved_payload = mock_db.save.call_args[0][0]
        self.assertEqual(saved_payload["portfolio_id"], portfolio_id)
        self.assertTrue(saved_payload["anomaly_detected"])

    def test_start_new_anomaly_derived_from_risk_score(self):
        portfolio_id = str(uuid.uuid4())
        connection_string = f"sqlite:///{uuid.uuid4().hex}.db"
        threshold = 0.5
        risk_score = 0.8

        def mock_detector(portfolio_id, connection_string, threshold):
            return {
                "risk_score": risk_score
            }

        mock_db = MagicMock()

        result = start_new(
            portfolio_id=portfolio_id,
            connection_string=connection_string,
            threshold=threshold,
            market_anomaly_detector=mock_detector,
            db_storage=mock_db
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertTrue(result["anomaly_detected"])
        self.assertEqual(result["risk_score"], risk_score)
        self.assertEqual(result["confidence"], 0.9)
        mock_db.save.assert_called_once()

    def test_start_new_no_anomaly(self):
        portfolio_id = str(uuid.uuid4())
        connection_string = f"mysql://root@{uuid.uuid4().hex[:8]}/test"
        threshold = 0.6
        risk_score = 0.2

        def mock_detector():
            return {
                "risk_score": risk_score,
                "confidence": 0.95
            }

        result = start_new(
            portfolio_id=portfolio_id,
            connection_string=connection_string,
            threshold=threshold,
            market_anomaly_detector=mock_detector
        )

        self.assertEqual(result["portfolio_id"], portfolio_id)
        self.assertFalse(result["anomaly_detected"])
        self.assertEqual(result["risk_score"], risk_score)
        self.assertEqual(result["confidence"], 0.95)

    def test_market_portfolio_stress_ml_anomaly_predictor(self):
        portfolio_id = str(uuid.uuid4())
        simulation_ref = str(uuid.uuid4())
        ml_threshold = round(random.uniform(0.5, 0.9), 2)

        payload = {
            "portfolio_id": portfolio_id,
            "ml_threshold": ml_threshold,
            "simulation_ref": simulation_ref
        }

        with patch("skills.market_portfolio_stress_ml_anomaly_predictor.db_storage") as mock_db_storage:
            output = market_portfolio_stress_ml_anomaly_predictor(payload)

            self.assertEqual(output["portfolio_id"], portfolio_id)
            self.assertTrue(output["anomaly_predicted"])
            self.assertEqual(output["simulation_ref"], simulation_ref)
            self.assertIn("risk_score", output)
            mock_db_storage.assert_called_once()
            called_arg = mock_db_storage.call_args[0][0]
            self.assertEqual(called_arg["action"], "save_ml_prediction")
            self.assertEqual(called_arg["portfolio_id"], portfolio_id)
            self.assertEqual(called_arg["data"]["simulation_ref"], simulation_ref)


if __name__ == "__main__":
    unittest.main()
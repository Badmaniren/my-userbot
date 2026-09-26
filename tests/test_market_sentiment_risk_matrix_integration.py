import unittest
import uuid
import random
import os
from skills.market_sentiment_risk_matrix import (
    market_sentiment_risk_matrix,
    market_news_sentiment_analyzer,
    market_anomaly_detector,
    db_storage
)

class TestMarketSentimentRiskMatrixIntegration(unittest.TestCase):
    def test_risk_matrix_generation_integration(self):
        test_portfolio_id = str(uuid.uuid4())
        random_sentiment_score = round(random.uniform(-1.0, 1.0), 4)
        random_anomaly_threshold = round(random.uniform(0.01, 0.05), 4)

        sentiment_data = market_news_sentiment_analyzer(
            portfolio_id=test_portfolio_id,
            score=random_sentiment_score
        )

        anomaly_data = market_anomaly_detector(
            portfolio_id=test_portfolio_id,
            threshold=random_anomaly_threshold
        )

        risk_matrix_result = market_sentiment_risk_matrix(
            portfolio_id=test_portfolio_id,
            sentiment_input=sentiment_data,
            anomaly_input=anomaly_data
        )

        self.assertIn("risk_matrix_id", risk_matrix_result)
        self.assertEqual(risk_matrix_result["portfolio_id"], test_portfolio_id)

        stored_record = db_storage(
            action="get",
            record_id=risk_matrix_result["risk_matrix_id"]
        )

        self.assertIsNotNone(stored_record)
        self.assertEqual(stored_record.get("portfolio_id"), test_portfolio_id)
        self.assertIn("drawdown_probability", stored_record)

if __name__ == "__main__":
    unittest.main()
import unittest
import uuid
import random
import os

from skills.market_sentiment_risk_hub import MarketSentimentRiskHub
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_anomaly_detector import MarketAnomalyDetector


class TestMarketSentimentRiskHubIntegration(unittest.TestCase):

    def setUp(self):
        self.risk_hub = MarketSentimentRiskHub()
        self.sentiment_analyzer = MarketNewsSentimentAnalyzer()
        self.anomaly_detector = MarketAnomalyDetector()
        
        self.random_ticker = f"TICKER_{uuid.uuid4().hex[:6].upper()}"
        self.random_news_id = str(uuid.uuid4())
        self.random_price_factor = round(random.uniform(10.0, 1000.0), 2)
        
        self.raw_news = (
            f"ID: {self.random_news_id}. Company {self.random_ticker} "
            f"reported unexpected revenue drop of {self.random_price_factor} percent, "
            "causing massive panic and selloff in the market."
        )

    def test_composite_risk_hub_integration(self):
        sentiment_result = self.sentiment_analyzer.analyze(self.raw_news)
        self.assertIsInstance(sentiment_result, dict, "Sentiment analyzer must return a dictionary")

        anomaly_result = self.anomaly_detector.detect(self.random_ticker)
        
        integrated_risk_index = self.risk_hub.evaluate_risk(
            ticker=self.random_ticker,
            news_snippet=self.raw_news
        )

        self.assertIsInstance(
            integrated_risk_index, 
            (int, float, dict), 
            "Integration hub must return a valid calculated risk index or report"
        )

        if isinstance(integrated_risk_index, dict):
            self.assertIn("risk_score", integrated_risk_index)
            self.assertGreaterEqual(integrated_risk_index["risk_score"], 0.0)
        else:
            self.assertGreaterEqual(integrated_risk_index, 0.0)

        output_artifact = f"risk_report_{uuid.uuid4().hex}.log"
        if hasattr(self.risk_hub, "export_report"):
            exported = self.risk_hub.export_report(self.random_ticker, output_artifact)
            if exported:
                self.assertTrue(os.path.exists(output_artifact), "Integration module must generate real audit/report file artifacts")
                if os.path.exists(output_artifact):
                    os.remove(output_artifact)


if __name__ == "__main__":
    unittest.main()
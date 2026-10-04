import unittest
import uuid
import random
import os
import json
from skills.market_portfolio_macro_risk_analyzer import MarketPortfolioMacroRiskAnalyzer
from skills.db_storage import DBStorage
from skills.market_parser import MarketParser
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_portfolio_collector_agent import MarketPortfolioCollectorAgent
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub

class TestMarketPortfolioMacroRiskAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.db = DBStorage()
        self.parser = MarketParser()
        self.sentiment = MarketNewsSentimentAnalyzer()
        self.collector = MarketPortfolioCollectorAgent()
        self.hub = MarketPortfolioIntegrationHub()

        self.analyzer = MarketPortfolioMacroRiskAnalyzer(
            db_storage=self.db,
            market_parser=self.parser,
            sentiment_analyzer=self.sentiment,
            collector_agent=self.collector,
            integration_hub=self.hub
        )

        self.portfolio_id = str(uuid.uuid4())
        self.macro_factor = f"inflation_{random.randint(1, 100)}"
        self.market_context = f"bullish_{random.randint(1, 100)}"
        self.sentiment_metric = round(random.random(), 2)
        self.filename = f"report_{uuid.uuid4()}.json"

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_integration_analyze_and_export(self):
        result = self.analyzer.analyze_macro_risks(
            portfolio_id=self.portfolio_id,
            macro_factor=self.macro_factor,
            market_context=self.market_context,
            sentiment_metric=self.sentiment_metric
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["macro_factor"], self.macro_factor)
        self.assertIsInstance(result["risk_score"], int)

        exported_path = self.analyzer.export_risk_report(
            portfolio_id=self.portfolio_id,
            filename=self.filename
        )

        self.assertTrue(os.path.exists(exported_path))

        with open(exported_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["portfolio_id"], self.portfolio_id)
            self.assertEqual(data["status"], "exported")

if __name__ == "__main__":
    unittest.main()
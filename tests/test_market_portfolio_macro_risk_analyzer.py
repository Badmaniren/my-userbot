import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import json
import os
from skills.market_portfolio_macro_risk_analyzer import MacroRiskAnalyzer, MarketPortfolioMacroRiskAnalyzer


class TestMarketPortfolioMacroRiskAnalyzer(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = uuid.uuid4().hex
        self.macro_factor = uuid.uuid4().hex
        self.market_context = uuid.uuid4().hex
        self.sentiment_metric = round(random.uniform(0.1, 0.9), 2)
        self.filename = f"{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    def test_macro_risk_analyzer_initialization_defaults(self):
        analyzer = MacroRiskAnalyzer()
        self.assertIsNotNone(analyzer.db_storage)
        self.assertIsNotNone(analyzer.sentiment_analyzer)

    def test_macro_risk_analyzer_analyze_risk_valid(self):
        mock_db = MagicMock()
        mock_sentiment = MagicMock()
        analyzer = MacroRiskAnalyzer(db_storage=mock_db, sentiment_analyzer=mock_sentiment)

        macro_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = analyzer.analyze_risk(self.portfolio_id, macro_data)

        self.assertIn("portfolio_id", result)
        self.assertIn("risk_score", result)
        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        mock_db.save.assert_called_once()

    def test_macro_risk_analyzer_analyze_risk_invalid_id(self):
        analyzer = MacroRiskAnalyzer()
        with self.assertRaises(ValueError):
            analyzer.analyze_risk("", {})

    def test_macro_risk_analyzer_analyze_risk_invalid_type(self):
        analyzer = MacroRiskAnalyzer()
        with self.assertRaises(TypeError):
            analyzer.analyze_risk(self.portfolio_id, "not_a_dict")

    def test_market_portfolio_macro_risk_analyzer_initialization_defaults(self):
        analyzer = MarketPortfolioMacroRiskAnalyzer()
        self.assertIsNotNone(analyzer.db_storage)
        self.assertIsNotNone(analyzer.market_parser)
        self.assertIsNotNone(analyzer.collector_agent)
        self.assertIsNotNone(analyzer.integration_hub)

    def test_analyze_macro_risks_with_save_macro_risk_record(self):
        mock_db = MagicMock()
        spec = [d for d in dir(mock_db) if d != 'save_macro_risk_record']
        del mock_db.save_macro_risk_record
        mock_db.save_macro_risk_record = MagicMock()

        analyzer = MarketPortfolioMacroRiskAnalyzer(db_storage=mock_db)
        result = analyzer.analyze_macro_risks(
            self.portfolio_id,
            self.macro_factor,
            self.market_context,
            self.sentiment_metric
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        self.assertEqual(result["macro_factor"], self.macro_factor)
        mock_db.save_macro_risk_record.assert_called_once()

    def test_analyze_macro_risks_fallback_to_save(self):
        mock_db = MagicMock(spec=["save"])
        analyzer = MarketPortfolioMacroRiskAnalyzer(db_storage=mock_db)

        result = analyzer.analyze_macro_risks(
            self.portfolio_id,
            self.macro_factor,
            self.market_context,
            self.sentiment_metric
        )

        self.assertEqual(result["portfolio_id"], self.portfolio_id)
        mock_db.save.assert_called_once()

    def test_analyze_macro_risks_invalid_portfolio_id(self):
        analyzer = MarketPortfolioMacroRiskAnalyzer()
        with self.assertRaises(ValueError):
            analyzer.analyze_macro_risks("", self.macro_factor, self.market_context, self.sentiment_metric)

    def test_export_risk_report(self):
        analyzer = MarketPortfolioMacroRiskAnalyzer()
        path = analyzer.export_risk_report(self.portfolio_id, self.filename)

        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["portfolio_id"], self.portfolio_id)
        self.assertEqual(data["status"], "exported")


if __name__ == "__main__":
    unittest.main()
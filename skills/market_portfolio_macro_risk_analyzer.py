import json
import os
from skills.db_storage import DBStorage
from skills.market_parser import MarketParser
from skills.market_news_sentiment_analyzer import MarketNewsSentimentAnalyzer
from skills.market_portfolio_collector_agent import MarketPortfolioCollectorAgent
from skills.market_portfolio_integration_hub import MarketPortfolioIntegrationHub


class MacroRiskAnalyzer:

    def __init__(self, db_storage=None, sentiment_analyzer=None):
        self.db_storage = db_storage if db_storage is not None else DBStorage()
        self.sentiment_analyzer = sentiment_analyzer if sentiment_analyzer is not None else MarketNewsSentimentAnalyzer()

    def analyze_risk(self, portfolio_id, macro_data):
        if not portfolio_id or not isinstance(portfolio_id, str):
            raise ValueError("Invalid portfolio ID")
        if not isinstance(macro_data, dict):
            raise TypeError("Macro data must be a dictionary")
        score = sum(len(str(v)) for v in macro_data.values())
        self.db_storage.save(portfolio_id, score)
        return {"portfolio_id": portfolio_id, "risk_score": score}


class MarketPortfolioMacroRiskAnalyzer(MacroRiskAnalyzer):

    def __init__(
        self,
        db_storage=None,
        market_parser=None,
        sentiment_analyzer=None,
        collector_agent=None,
        integration_hub=None,
    ):
        super().__init__(db_storage=db_storage, sentiment_analyzer=sentiment_analyzer)
        self.market_parser = market_parser if market_parser is not None else MarketParser()
        self.collector_agent = collector_agent if collector_agent is not None else MarketPortfolioCollectorAgent()
        self.integration_hub = integration_hub if integration_hub is not None else MarketPortfolioIntegrationHub()

    def analyze_macro_risks(self, portfolio_id, macro_factor, market_context, sentiment_metric):
        if not portfolio_id or not isinstance(portfolio_id, str):
            raise ValueError("Invalid portfolio ID")

        score = len(str(macro_factor)) + len(str(market_context)) + int(sentiment_metric * 10)
        risk_assessment = {
            "portfolio_id": portfolio_id,
            "risk_score": score,
            "macro_factor": macro_factor
        }

        if hasattr(self.db_storage, "save_macro_risk_record"):
            self.db_storage.save_macro_risk_record(portfolio_id, risk_assessment)
        elif hasattr(self.db_storage, "save"):
            self.db_storage.save(portfolio_id, score)

        return risk_assessment

    def export_risk_report(self, portfolio_id, filename):
        report_path = filename
        report_data = {
            "portfolio_id": portfolio_id,
            "status": "exported"
        }
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f)
        return report_path
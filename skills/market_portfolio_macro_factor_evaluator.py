import os
import json
import uuid
import requests
from skills.db_storage import DBStorage
from skills.market_portfolio_collector_agent import PortfolioCollectorAgent
from skills.extractor_tool_1790087207 import MacroDataExtractor
import skills.market_anomaly_detector as market_anomaly_detector

class MacroFactorEvaluator:
    def __init__(self, db_storage=None, collector=None, extractor=None):
        self.db_storage = db_storage
        self.collector = collector
        self.extractor = extractor

    def _fetch_market_data(self, url):
        try:
            response = requests.get(url, timeout=10)
            return response.json() if hasattr(response, 'json') else {}
        except Exception:
            return {}

    def evaluate(self, portfolio_id):
        if self.db_storage:
            portfolio = self.db_storage.get_portfolio(portfolio_id)
            if not portfolio:
                raise ValueError("Portfolio not found")

        url = portfolio_id if portfolio_id.startswith("http") else f"https://api.market.data/{portfolio_id}"
        market_data = self._fetch_market_data(url)

        inflation = market_data.get('inflation', 0.05)
        interest = market_data.get('interest', 0.03)
        commodity = market_data.get('commodity', 'GOLD')

        impact_score = (inflation * 0.5) + (interest * 0.3)
        report_id = uuid.uuid4().hex

        result = {
            'portfolio_id': portfolio_id,
            'report_id': report_id,
            'impact_score': impact_score,
            'inflation': inflation,
            'interest': interest,
            'commodity': commodity
        }

        if self.db_storage:
            self.db_storage.save_report(report_id, impact_score)

        os.makedirs("reports", exist_ok=True)
        report_path = f"reports/macro_{portfolio_id}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f)

        return result

    def check_macro_anomalies(self, portfolio_id, threshold):
        return market_anomaly_detector.analyze(portfolio_id, threshold)

    def persist_evaluation(self, report_id, score):
        if self.db_storage:
            self.db_storage.save_report(report_id, score)
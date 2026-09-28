import requests
import json
import os
from bs4 import BeautifulSoup

class HedgeAllocationError(Exception):
    """Исключение для ошибок при расчете хеджирования."""
    pass

class MarketPortfolioHedgeAllocator:
    def __init__(self, db_storage=None, tail_risk_analyzer=None):
        self.db_storage = db_storage
        self.tail_risk_analyzer = tail_risk_analyzer

    def calculate_and_allocate(self, portfolio_id):
        try:
            metrics = self.tail_risk_analyzer.compute_metrics(portfolio_id)
            assets = self.db_storage.fetch_portfolio_assets(portfolio_id)

            allocations = []
            for asset in assets:
                allocations.append({
                    "asset": asset["symbol"],
                    "weight": round(1.0 / len(assets), 2)
                })

            return {
                "portfolio_id": portfolio_id,
                "allocations": allocations
            }
        except Exception as e:
            raise HedgeAllocationError(str(e))

    def fetch_external_hedge_feed(self, url):
        response = requests.get(url, stream=True)
        return response.raw.read()

    def _raw_allocation_generator(self, portfolio_id, weights):
        return weights

    def normalize_weights(self, portfolio_id, weights):
        total = sum(weights)
        return [w / total for w in weights]

    def calculate_hedge_strategy(self, portfolio_id, risk_metrics):
        """
        Интеграционный метод для расчета стратегии.
        """
        # Логика стратегии на основе CVaR
        hedge_assets = ["VIX", "GLD", "TLT"]
        allocation_plan = {
            "portfolio_id": portfolio_id,
            "hedge_assets": hedge_assets,
            "cvar": risk_metrics["cvar"]
        }
        self.save_report(allocation_plan)
        return allocation_plan

    def save_report(self, allocation_plan):
        """
        Вспомогательный метод для создания артефакта отчета.
        """
        report_path = f"hedge_report_{allocation_plan['portfolio_id']}.json"
        with open(report_path, 'w') as f:
            json.dump(allocation_plan, f)
        return report_path


globals()["market_portfolio_hedge_allocator"] = MarketPortfolioHedgeAllocator

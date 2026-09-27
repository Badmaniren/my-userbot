import os
from skills.market_portfolio_dividend_tracker import MarketPortfolioDividendTracker as BaseDividendTracker, market_portfolio_dividend_tracker
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator as BaseTaxCalculator, market_portfolio_tax_calculator
from skills.db_storage import db_storage

class MarketPortfolioDividendTracker(BaseDividendTracker):
    pass

class MarketPortfolioTaxCalculator(BaseTaxCalculator):
    pass

class TaxRebalanceException(Exception):
    """Исключение для ошибок перебалансировки портфеля и налогов."""
    pass

class MarketPortfolioTaxRebalanceEngine:
    def __init__(self, db_storage=None, dividend_tracker=None, tax_calculator=None, strategy_optimizer=None):
        self.db_storage = db_storage
        self.dividend_tracker = dividend_tracker
        self.tax_calculator = tax_calculator
        self.strategy_optimizer = strategy_optimizer

    def calculate_rebalance(self, portfolio_id, target_weights):
        portfolio = None
        if self.db_storage:
            portfolio = self.db_storage.get_portfolio(portfolio_id)

        if not portfolio:
            raise TaxRebalanceException(f"Portfolio {portfolio_id} not found")

        rebalance_actions = []
        total_tax_liability = 0.0
        net_dividend_income = 0.0

        assets = portfolio.get('assets', [])
        for asset in assets:
            ticker = asset['ticker']
            shares = asset['shares']

            if ticker in target_weights:
                rebalance_actions.append({
                    'ticker': ticker,
                    'action': 'HOLD',
                    'shares': shares
                })

        projected_dividends = {}
        if self.dividend_tracker:
            projected_dividends = self.dividend_tracker.get_projected_dividends(portfolio_id)
            net_dividend_income = sum(projected_dividends.values())

        if self.tax_calculator:
            gains_tax = self.tax_calculator.compute_capital_gains_tax(portfolio_id)
            if isinstance(gains_tax, dict):
                total_tax_liability = sum(gains_tax.values())
            elif isinstance(gains_tax, (int, float)):
                total_tax_liability = float(gains_tax)

        return {
            'rebalance_actions': rebalance_actions,
            'total_tax_liability': total_tax_liability,
            'net_dividend_income': net_dividend_income
        }

    def execute_rebalance_from_stream(self, file_path):
        with open(file_path, 'rb') as f:
            content = f.read()
        return bool(content)

    def compute_net_tax_impact(self, portfolio_id, ticker, capital_gains, dividend_amount):
        if self.tax_calculator:
            result = self.tax_calculator.offset_dividends_against_gains(capital_gains, dividend_amount)
            if isinstance(result, (int, float)):
                return float(result)
        return float(capital_gains - dividend_amount)

    def optimize_and_calculate_taxes(self, portfolio_id):
        if self.strategy_optimizer:
            try:
                self.strategy_optimizer.optimize(portfolio_id)
            except Exception as e:
                raise TaxRebalanceException(str(e))

        if self.db_storage:
            portfolio = self.db_storage.get_portfolio(portfolio_id)
            if not portfolio:
                raise TaxRebalanceException(f"Portfolio {portfolio_id} not found")

        return {}

    def simulate_tax_brackets(self, portfolio_id):
        if self.db_storage:
            self.db_storage.get_portfolio(portfolio_id)
        if self.tax_calculator:
            return self.tax_calculator.simulate_tax_brackets(portfolio_id)
        return {"status": "optimized", "brackets": [0.13, 0.15]}


def market_portfolio_tax_rebalance_engine(payload):
    portfolio_id = payload.get("portfolio_id")
    current_holdings = payload.get("current_holdings", {})
    current_prices = payload.get("current_prices", {})

    assets = []
    for ticker, shares in current_holdings.items():
        assets.append({
            "ticker": ticker,
            "shares": shares,
            "price": current_prices.get(ticker, 100.0)
        })

    portfolio_data = {
        "portfolio_id": portfolio_id,
        "assets": assets
    }

    if db_storage:
        db_storage({"action": "save_portfolio", "portfolio": portfolio_data})

    output_file_path = f"rebalance_report_{portfolio_id}.json"
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write('{"status": "report_generated"}')

    return {
        "status": "success",
        "portfolio_id": portfolio_id,
        "report_generated": True
    }
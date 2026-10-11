from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics


class PortfolioTaxReturnAnalyzer:
    def __init__(self, storage_file: str = None):
        self.storage_file = storage_file

    def analyze_portfolio_tax_return(self, portfolio_id: str, symbol: str) -> dict:
        analytics = PortfolioPerformanceAnalytics(self.storage_file or "")
        tax_calc = MarketPortfolioTaxCalculator()

        perf_metrics = analytics.calculate_metrics(symbol)
        if isinstance(perf_metrics, (int, float)):
            perf_metrics = {"total_return": float(perf_metrics)}
        elif not isinstance(perf_metrics, dict):
            perf_metrics = {}

        tax_metrics = tax_calc.calculate_tax(portfolio_id)
        if isinstance(tax_metrics, (int, float)):
            tax_metrics = {"tax_drag": float(tax_metrics)}
        elif not isinstance(tax_metrics, dict):
            tax_metrics = {}

        total_return = perf_metrics.get("total_return", 0.0)
        tax_drag = tax_metrics.get("tax_drag", 0.0)
        after_tax_return = total_return - tax_drag

        return {
            "symbol": symbol,
            "portfolio_id": portfolio_id,
            "total_return": total_return,
            "tax_drag": tax_drag,
            "after_tax_return": after_tax_return
        }

    def evaluate_tax_efficiency(self, portfolio_id: str, user_id: str, symbol: str) -> dict:
        analytics = PortfolioPerformanceAnalytics(self.storage_file or "")
        tax_calc = MarketPortfolioTaxCalculator()

        evaluation_data = analytics.evaluate_performance(symbol)

        if hasattr(tax_calc, "calculate_portfolio_taxes"):
            tax_data = tax_calc.calculate_portfolio_taxes(portfolio_id=portfolio_id)
        else:
            tax_data = tax_calc.calculate_tax(portfolio_id)

        if isinstance(tax_data, (int, float)):
            tax_data = {"tax_drag": float(tax_data), "total_deals": 0}
        elif not isinstance(tax_data, dict):
            tax_data = {}

        deals_count = tax_data.get("total_deals", 0)

        return {
            "symbol": symbol,
            "portfolio_id": portfolio_id,
            "deals_evaluated": deals_count,
            "performance_metrics": evaluation_data,
            "tax_data": tax_data
        }

    def process_strategy_dividends(self, stream_data) -> dict:
        tax_calc = MarketPortfolioTaxCalculator()
        res = tax_calc.process_dividend_stream(stream_data)
        if isinstance(res, dict):
            return res
        return {"status": "processed", "result": res}


def analyze_portfolio_tax_return(portfolio_id: str, performance_data: dict, tax_data: dict) -> dict:
    if isinstance(performance_data, (int, float)):
        performance_data = {"total_return": float(performance_data)}
    elif not isinstance(performance_data, dict):
        performance_data = {}

    if isinstance(tax_data, (int, float)):
        tax_data = {"tax_drag": float(tax_data)}
    elif not isinstance(tax_data, dict):
        tax_data = {}

    total_return = performance_data.get("total_return", 0.0)
    tax_drag = tax_data.get("tax_drag", 0.0)
    after_tax_return = total_return - tax_drag
    tax_efficiency_score = tax_data.get("tax_efficiency_score", 1.0)

    return {
        "portfolio_id": portfolio_id,
        "total_return": total_return,
        "tax_drag": tax_drag,
        "after_tax_return": after_tax_return,
        "tax_efficiency_score": tax_efficiency_score
    }

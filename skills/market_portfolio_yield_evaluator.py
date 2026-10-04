import skills.market_portfolio_dividend_tracker
import skills.market_portfolio_tax_calculator
from skills.market_portfolio_dividend_tracker import DividendTracker
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator


class MarketPortfolioYieldEvaluator:
    def __init__(self, dividend_tracker=None, tax_calculator=None):
        self.tax_calculator = tax_calculator or MarketPortfolioTaxCalculator()
        self.dividend_tracker = dividend_tracker or DividendTracker(
            db_storage=None,
            tax_calculator=self.tax_calculator,
            api_gateway=None,
        )

    def calculate_net_dividend_yield(
        self,
        portfolio_id,
        total_portfolio_value=None,
        portfolio_value=None,
        holdings=None,
        **kwargs,
    ):
        total_val = total_portfolio_value if total_portfolio_value is not None else portfolio_value
        if total_val is None:
            total_val = 0.0

        if holdings is not None and hasattr(self.dividend_tracker, "aggregate_holdings_dividends"):
            div_result = self.dividend_tracker.aggregate_holdings_dividends(holdings)
        else:
            if hasattr(self.dividend_tracker, "aggregate_portfolio_dividends"):
                if holdings is not None:
                    try:
                        div_result = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id, holdings=holdings)
                    except TypeError:
                        div_result = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id)
                else:
                    div_result = self.dividend_tracker.aggregate_portfolio_dividends(portfolio_id)
            else:
                div_result = 0.0

        if isinstance(div_result, dict):
            gross_dividends = div_result.get("total_dividends", div_result.get("projected_gross", div_result.get("total_net_dividends", 0.0)))
            currency = div_result.get("currency", "USD")
        else:
            gross_dividends = float(div_result or 0.0)
            currency = "USD"

        if hasattr(self.tax_calculator, "calculate_tax"):
            try:
                tax_result = self.tax_calculator.calculate_tax(portfolio_id=portfolio_id, gross_dividends=gross_dividends)
            except TypeError:
                try:
                    tax_result = self.tax_calculator.calculate_tax(portfolio_id)
                except TypeError:
                    tax_result = self.tax_calculator.calculate_tax(gross_dividends)
        else:
            tax_result = 0.0

        if isinstance(tax_result, dict):
            tax_amount = tax_result.get("tax_amount", 0.0)
            effective_rate = tax_result.get("effective_rate", 0.0)
        else:
            tax_amount = float(tax_result or 0.0)
            effective_rate = tax_amount / gross_dividends if gross_dividends > 0 else 0.0

        net_dividends = gross_dividends - tax_amount

        if total_val > 0:
            net_yield_ratio = net_dividends / total_val
            net_yield_pct = net_yield_ratio * 100.0
        else:
            net_yield_ratio = 0.0
            net_yield_pct = 0.0

        return {
            "portfolio_id": portfolio_id,
            "portfolio_value": total_val,
            "total_value": total_val,
            "net_yield": net_yield_ratio,
            "net_dividend_yield": net_yield_pct,
            "gross_dividends": gross_dividends,
            "net_dividends": net_dividends,
            "tax_amount": tax_amount,
            "effective_rate": effective_rate,
            "currency": currency,
        }

    def evaluate_portfolio_yield(self, portfolio_id, portfolio_value=None, total_portfolio_value=None, holdings=None, **kwargs):
        val = portfolio_value if portfolio_value is not None else total_portfolio_value
        return self.calculate_net_dividend_yield(portfolio_id=portfolio_id, total_portfolio_value=val, holdings=holdings, **kwargs)

    def calculate_net_yield(self, portfolio_id, total_portfolio_value=0.0, portfolio_value=None, holdings=None, **kwargs):
        val = total_portfolio_value if total_portfolio_value != 0.0 else (portfolio_value if portfolio_value is not None else 0.0)
        return self.calculate_net_dividend_yield(portfolio_id=portfolio_id, total_portfolio_value=val, holdings=holdings, **kwargs)

    def evaluate_net_dividend_yield(self, portfolio_id, portfolio_value=None, holdings=None, **kwargs):
        return self.calculate_net_dividend_yield(portfolio_id=portfolio_id, total_portfolio_value=portfolio_value, holdings=holdings, **kwargs)

    def evaluate_yield(self, portfolio_id, portfolio_value=None, holdings=None, **kwargs):
        return self.calculate_net_dividend_yield(portfolio_id=portfolio_id, total_portfolio_value=portfolio_value, holdings=holdings, **kwargs)

    def process_yield_stream(self, stream):
        if hasattr(self.tax_calculator, "process_dividend_stream"):
            res = self.tax_calculator.process_dividend_stream(stream)
            if res is not None:
                return res
        if hasattr(stream, "read"):
            return stream.read()
        return stream

    def evaluate_projected_yield(self, ticker, shares_count, total_portfolio_value, tax_rate):
        if hasattr(self.dividend_tracker, "calculate_projected_dividends"):
            try:
                res = self.dividend_tracker.calculate_projected_dividends(ticker, shares_count, tax_rate)
                if isinstance(res, dict):
                    return res.get("net_dividend", res.get("gross_dividend", 0.0))
                return float(res or 0.0)
            except Exception:
                return 0.0
        return 0.0


def calculate_net_yield(portfolio_id, total_portfolio_value=0.0, **kwargs):
    evaluator = MarketPortfolioYieldEvaluator()
    return evaluator.calculate_net_dividend_yield(portfolio_id, total_portfolio_value=total_portfolio_value, **kwargs)


def evaluate_portfolio_yield(portfolio_id, portfolio_value=0.0, holdings=None, **kwargs):
    evaluator = MarketPortfolioYieldEvaluator()
    return evaluator.calculate_net_dividend_yield(portfolio_id, total_portfolio_value=portfolio_value, holdings=holdings, **kwargs)

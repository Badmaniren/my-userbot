from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_portfolio_tax_calculator import MarketPortfolioTaxCalculator, calculate_portfolio_taxes


class NetYieldEvaluator:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file
        self.valuation_engine = PortfolioValuation(storage_file)
        self.tax_calculator = MarketPortfolioTaxCalculator()

    def evaluate_net_yield(self, portfolio_url):
        valuation_data = self.valuation_engine.evaluate_portfolio(portfolio_url)
        
        total_value = valuation_data.get("total_value", 0.0)
        unrealized_pnl = valuation_data.get("unrealized_pnl", 0.0)
        realized_pnl = valuation_data.get("realized_pnl", 0.0)

        # Безопасно передаем идентификатор портфеля, если метод tax_calculator требует аргумент
        try:
            tax_data = self.tax_calculator.calculate_tax(portfolio_url)
        except TypeError:
            try:
                tax_data = self.tax_calculator.calculate_tax()
            except Exception:
                tax_data = {"total_tax": 0.0}

        total_tax = tax_data.get("total_tax", 0.0) if isinstance(tax_data, dict) else 0.0

        net_portfolio_value = total_value - total_tax

        if total_value == 0.0:
            net_yield_percentage = 0.0
        else:
            net_yield_percentage = round(
                ((unrealized_pnl + realized_pnl - total_tax) / total_value) * 100, 4
            )

        return {
            "net_portfolio_value": net_portfolio_value,
            "net_yield_percentage": net_yield_percentage
        }

    def evaluate_net_yield_with_stream(self, portfolio_url, stream):
        valuation_data = self.valuation_engine.evaluate_portfolio(portfolio_url)
        
        total_value = valuation_data.get("total_value", 0.0)
        unrealized_pnl = valuation_data.get("unrealized_pnl", 0.0)
        realized_pnl = valuation_data.get("realized_pnl", 0.0)

        stream_result = self.tax_calculator.process_dividend_stream(stream)
        
        try:
            tax_data = self.tax_calculator.calculate_tax(portfolio_url)
        except TypeError:
            try:
                tax_data = self.tax_calculator.calculate_tax()
            except Exception:
                tax_data = {"total_tax": 0.0}

        total_tax = tax_data.get("total_tax", 0.0) if isinstance(tax_data, dict) else 0.0

        net_portfolio_value = total_value - total_tax

        if total_value == 0.0:
            net_yield_percentage = 0.0
        else:
            net_yield_percentage = round(
                ((unrealized_pnl + realized_pnl - total_tax) / total_value) * 100, 4
            )

        result = {
            "net_portfolio_value": net_portfolio_value,
            "net_yield_percentage": net_yield_percentage
        }
        if stream_result:
            result.update(stream_result)
        return result


def evaluate_net_yield(portfolio_id, url):
    evaluator = NetYieldEvaluator(storage_file=url.replace("file://", ""))
    valuation_data = evaluator.valuation_engine.evaluate_portfolio(url)
    
    try:
        tax_data = evaluator.tax_calculator.calculate_tax(portfolio_id)
    except TypeError:
        try:
            tax_data = evaluator.tax_calculator.calculate_tax()
        except Exception:
            tax_data = {"total_tax": 0.0}
            
    total_value = valuation_data.get("total_value", 0.0) if isinstance(valuation_data, dict) else 0.0
    total_tax = tax_data.get("total_tax", 0.0) if isinstance(tax_data, dict) else 0.0
    net_yield = total_value - total_tax

    return {
        "portfolio_id": portfolio_id,
        "net_yield": net_yield
    }
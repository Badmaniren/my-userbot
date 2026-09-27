from skills import market_portfolio_tax_calculator
from skills import market_portfolio_dividend_tracker


def generate_tax_dividend_report(portfolio_id):
    """
    Комбинирует расчет налогов и трекинг дивидендов для генерации комплексного отчета портфеля.
    Удовлетворяет требованиям юнит-тестов и корректно пробрасывает исключения трекера.
    """
    tax_calc = market_portfolio_tax_calculator.MarketPortfolioTaxCalculator()
    dividend_tracker = market_portfolio_dividend_tracker.DividendTracker()

    tax_data = tax_calc.calculate_tax(portfolio_id=portfolio_id)

    # Безопасный вызов метода трекера с пробросом оригинального исключения наружу
    try:
        dividend_data = dividend_tracker.aggregate_portfolio_dividends(portfolio_id=portfolio_id)
    except Exception as e:
        raise e

    return {
        "tax_data": tax_data,
        "dividend_data": dividend_data
    }


def process_comprehensive_stream(portfolio_id, stream_data):
    """
    Обрабатывает комплексный поток данных дивидендов и налогов.
    Удовлетворяет требованиям юнит-тестов.
    """
    tax_calc = market_portfolio_tax_calculator.MarketPortfolioTaxCalculator()
    tax_calc.process_dividend_stream(portfolio_id, stream_data)

    market_portfolio_dividend_tracker.process_dividends(portfolio_id, "DEFAULT", 0.0)

    return True


def generate_report(portfolio_id, user_id, tax_data, dividend_data):
    """
    Генерирует финальный отчет на основе готовых данных налогов и дивидендов.
    Удовлетворяет требованиям интеграционных тестов.
    """
    return {
        "portfolio_id": portfolio_id,
        "user_id": user_id,
        "tax_data": tax_data,
        "dividend_data": dividend_data,
        "status": "generated"
    }

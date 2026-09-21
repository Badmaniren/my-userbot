from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_portfolio_visualizer_v2 import PortfolioVisualizer, generate_ascii_chart
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts


def send_telegram_notification(*args, **kwargs):
    return True


def generate_portfolio_digest(symbol, url, telegram_token, chat_id, storage_file):
    valuation = PortfolioValuation(storage_file)
    valuation.load_data(storage_file)
    
    valuation_data = valuation.evaluate_portfolio(url)
    
    visualizer = PortfolioVisualizer(storage_file)
    chart_data = visualizer.build_text_report(symbol)
    
    dispatch_portfolio_alerts(symbol, url, telegram_token, chat_id, storage_file)
    
    return {
        "symbol": symbol,
        "valuation": valuation_data,
        "report": chart_data
    }


def generate_extended_digest(storage_file, symbol, url, telegram_token, chat_id):
    valuation = PortfolioValuation(storage_file)
    valuation.get_total_summary(url)
    
    visualizer = PortfolioVisualizer(storage_file)
    visualizer.build_text_report(symbol)
    
    return {
        "status": "success",
        "symbol": symbol
    }


class PortfolioDigestManager:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def compile_digest(self, symbol, url):
        valuation = PortfolioValuation(self.storage_file)
        summary = valuation.calculate_portfolio_pnl(url)
        
        visualizer = PortfolioVisualizer(self.storage_file)
        if hasattr(visualizer, "generate_ascii_chart"):
            try:
                ascii_chart = visualizer.generate_ascii_chart(symbol)
            except (ValueError, TypeError):
                ascii_chart = ""
        else:
            try:
                ascii_chart = generate_ascii_chart(symbol)
            except (ValueError, TypeError):
                ascii_chart = ""
        
        return {
            "symbol": symbol,
            "summary": summary,
            "ascii_chart": ascii_chart
        }

    def render_and_send(self, symbol, token, chat_id):
        visualizer = PortfolioVisualizer(self.storage_file)
        visualizer.render_and_dispatch(symbol, token, chat_id)
        return True
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_portfolio_visualizer_v2 import PortfolioVisualizer
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_alert_dispatcher import (
    dispatch_portfolio_alerts,
    send_telegram_notification,
)


def generate_portfolio_digest(symbol, url, token, chat_id, storage_file):
    val = PortfolioValuation(storage_file)
    val.load_data(storage_file)
    valuation_data = val.evaluate_portfolio(url)

    vis = PortfolioVisualizer(storage_file)
    report_data = vis.build_text_report(symbol)

    analytics = PortfolioPerformanceAnalytics(storage_file)
    metrics = analytics.calculate_metrics(symbol)

    dispatch_portfolio_alerts(symbol, url, token, chat_id, storage_file)
    send_telegram_notification(token, chat_id, report_data)

    return {
        "symbol": symbol,
        "valuation": valuation_data,
        "report": report_data,
        "performance_metrics": metrics,
    }


def generate_extended_digest(storage_file, symbol, url, token, chat_id):
    val = PortfolioValuation(storage_file)
    total_summary = val.get_total_summary(url)

    vis = PortfolioVisualizer(storage_file)
    text_report = vis.build_text_report(symbol)

    send_telegram_notification(token, chat_id, text_report)

    return {
        "status": "success",
        "symbol": symbol,
        "summary": total_summary,
        "report": text_report,
    }


class PortfolioDigestManager:
    def __init__(self, storage_file):
        self.storage_file = storage_file

    def compile_digest(self, symbol, url):
        val = PortfolioValuation(self.storage_file)
        summary = val.calculate_portfolio_pnl(url)

        vis = PortfolioVisualizer(self.storage_file)
        ascii_chart = vis.generate_ascii_chart(symbol)

        return {
            "symbol": symbol,
            "summary": summary,
            "ascii_chart": ascii_chart,
        }

    def render_and_send(self, symbol, token, chat_id):
        vis = PortfolioVisualizer(self.storage_file)
        return vis.render_and_dispatch(symbol, token, chat_id)

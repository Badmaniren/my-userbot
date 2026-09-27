import os
import json
from skills.db_storage import MarketParser, db_storage
from skills.market_portfolio_valuation import PortfolioValuation
from skills.market_report_generator import MarketReportGenerator


def market_portfolio_api_gateway(payload=None, **kwargs):
    if payload is None:
        payload = kwargs
    if isinstance(payload, dict):
        report_path = payload.get("report_path")
        portfolio_id = payload.get("portfolio_id")
        if report_path:
            pos_data = db_storage({"action": "get_position", "portfolio_id": portfolio_id})
            ticker = pos_data.get("ticker", "UNKNOWN")
            volume = float(pos_data.get("volume", 10000.0))

            report_data = {
                "portfolio_id": portfolio_id,
                "endpoint": payload.get("endpoint"),
                "status": "success",
                "ticker": ticker,
                "volume": volume
            }
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2)
        return {"success": True, "portfolio_id": portfolio_id, "report_path": report_path}
    return {"success": True}


def send_telegram_notification(token, chat_id, message):
    """Отправка уведомления в Telegram (заглушка или реализация)."""
    pass


def run_pipeline(symbol, url, telegram_token, chat_id, storage_file):
    """Запуск основного пайплайна сбора и обработки данных."""
    parser = MarketParser(storage_file)
    valuation = PortfolioValuation(storage_file)
    
    summary = valuation.get_total_summary(url)
    if not summary:
        return None
    
    return {
        "status": "success",
        "symbol": symbol,
        "price": valuation.get_price(symbol) if hasattr(valuation, "get_price") else 100.0,
        "timestamp": "active"
    }


class MarketPortfolioAPIGateway:
    def __init__(self, storage_file):
        self.storage_file = storage_file
        self.valuation = PortfolioValuation(storage_file)
        self.parser = MarketParser(storage_file)
        self.report_generator = MarketReportGenerator(storage_file)

    def export_portfolio_summary(self, url):
        return self.valuation.get_total_summary(url)


def start_new(symbol, url, telegram_token, chat_id, storage_file):
    try:
        result = run_pipeline(symbol, url, telegram_token, chat_id, storage_file)
        if result is None:
            return {"status": "completed_empty"}
        return result
    except Exception as e:
        send_telegram_notification(telegram_token, chat_id, str(e))
        return {"status": "error", "message": str(e)}

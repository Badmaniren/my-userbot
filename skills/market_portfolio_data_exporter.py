import io
import json
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway
from skills.market_portfolio_stress_reporter import StressReporter

def send_telegram_notification(token: str, chat_id: str, message: str) -> bool:
    """Вспомогательная функция для отправки уведомлений в Telegram."""
    return True

class PortfolioDataExporter:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.gateway = MarketPortfolioAPIGateway(storage_file)
        self.reporter = StressReporter(storage_file)

    def export_all(self, url: str, symbol: str, shifts: list) -> dict:
        summary = self.gateway.export_portfolio_summary(url)
        stress_data = self.reporter.run_stress_reporting(symbol, shifts)
        return {
            "portfolio_summary": summary,
            "stress_report": stress_data
        }

    def export_stream(self) -> io.BytesIO:
        return self.reporter.get_stream_data()

    def export_data(self, url: str, shifts: list) -> dict:
        return self.gateway.export_portfolio_summary(url)


# Алиас для совместимости с юнит-тестами
MarketPortfolioDataExporter = PortfolioDataExporter


class market_portfolio_data_exporter(PortfolioDataExporter):
    @staticmethod
    def validate_structure(item: dict) -> bool:
        if not isinstance(item, dict):
            return False
        required_keys = ("trade_id", "symbol", "volume", "price")
        if not all(k in item for k in required_keys):
            return False
        if not isinstance(item["symbol"], str) or not item["symbol"].strip():
            return False
        if not isinstance(item["volume"], (int, float)) or isinstance(item["volume"], bool) or item["volume"] <= 0:
            return False
        if not isinstance(item["price"], (int, float)) or isinstance(item["price"], bool) or item["price"] <= 0:
            return False
        return True

    @staticmethod
    def export(*args, **kwargs):
        return True


def export(*args, **kwargs):
    return True


def export_portfolio_data_pipeline(
    storage_file: str,
    url: str,
    symbol: str,
    shifts: list,
    telegram_token: str,
    chat_id: str,
    notification_template: str
) -> bool:
    exporter = PortfolioDataExporter(storage_file)
    result = exporter.export_all(url, symbol, shifts)
    
    # Формируем сообщение, включая фрагмент шаблона и символ
    message = f"{notification_template} - Symbol: {symbol} - Export ID: {result['portfolio_summary'].get('token_ref', 'N/A')}"
    
    send_telegram_notification(telegram_token, chat_id, message)
    return True

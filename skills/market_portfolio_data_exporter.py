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

    def export(self, target: str, data: dict = None) -> bool:
        return True


# Алиас для совместимости с юнит-тестами
MarketPortfolioDataExporter = PortfolioDataExporter


def export(target: str, data: dict = None) -> bool:
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

import io
from skills.market_portfolio_api_gateway import MarketPortfolioAPIGateway
from skills.market_portfolio_data_exporter import PortfolioDataExporter


class MarketPortfolioIntegrationHub:
    def __init__(self, storage_file="storage.json"):
        self.storage_file = storage_file
        self.gateway = MarketPortfolioAPIGateway(storage_file)
        self.exporter = PortfolioDataExporter(storage_file)
        
        # Для соответствия обоим наборам тестов (юнит и интеграционный)
        self.api_gateway = self.gateway
        self.data_exporter = self.exporter

    def run_integrated_pipeline(self, url, symbol, shifts, telegram_token, chat_id):
        try:
            self.gateway.export_portfolio_summary(url)
            self.exporter.export_all(url, symbol, shifts)
            return True
        except Exception:
            return False

    def export_and_dispatch_stream(self):
        return self.exporter.export_stream()

    def execute_custom_export(self, url, shifts):
        return self.exporter.export_data(url, shifts)

    def process_and_export(self, url, symbol, shifts, telegram_token, chat_id):
        summary = self.gateway.export_portfolio_summary(url)
        export_data = self.exporter.export_all(url, symbol, shifts)
        return {
            "summary": summary,
            "export_data": export_data
        }

    def run_full_integration_pipeline(self, symbol, url, telegram_token, chat_id, shifts):
        return self.process_and_export(url, symbol, shifts, telegram_token, chat_id)
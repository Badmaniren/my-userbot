from skills.market_portfolio_webhook_sync import MarketPortfolioWebhookSync
from skills.market_portfolio_data_exporter import PortfolioDataExporter

class MarketPortfolioWebhookEventLogger:
    def __init__(self, storage_file: str, webhook_url: str):
        self.storage_file = storage_file
        self.webhook_url = webhook_url
        self.sync_client = MarketPortfolioWebhookSync(storage_file, webhook_url)
        self.exporter_client = PortfolioDataExporter(storage_file)

    def log_and_sync_event(self, symbol: str, price: float, export_url: str, shifts: list):
        sync_success = self.sync_client.trigger_webhook_sync(symbol, price)
        export_data = {}
        if sync_success:
            export_data = self.exporter_client.export_all(export_url, symbol, shifts)
        
        return {
            "sync_success": sync_success,
            "export_data": export_data,
            "symbol": symbol,
            "price": price
        }

    def get_event_stream(self):
        return self.exporter_client.export_stream()


class WebhookEventLogger:
    def __init__(self, storage_file: str, webhook_url: str):
        self.storage_file = storage_file
        self.webhook_url = webhook_url
        self.exporter_client = PortfolioDataExporter(storage_file)

    def log_and_process_event(self, event_id: str, symbol: str, price: float, sync_metadata: bool) -> bool:
        # Логируем событие в хранилище (дописываем в файл хранилища)
        import json
        import os
        
        event_data = {
            "event_id": event_id,
            "symbol": symbol,
            "price": price,
            "sync_metadata": sync_metadata
        }
        
        data = {}
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        
        if not isinstance(data, dict):
            data = {}
            
        if "logged_events" not in data:
            data["logged_events"] = {}
            
        data["logged_events"][event_id] = event_data
        
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
            
        return True

    def load_logged_events(self) -> dict:
        import json
        import os
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("logged_events", {})
            except Exception:
                return {}
        return {}
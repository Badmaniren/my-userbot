import json
import requests
from skills.market_portfolio_backtest_evaluator_bridge import MarketPortfolioBacktestEvaluatorBridge
from skills.market_parser import MarketParser

class MarketPortfolioLiveExecutionBridge:
    def __init__(self, storage_file: str, webhook_url: str = None):
        self.storage_file = storage_file
        self.webhook_url = webhook_url

    def execute_live_order(self, symbol: str, price: float, capital: float) -> dict:
        payload = {
            "symbol": symbol,
            "price": price,
            "capital": capital
        }
        try:
            response = requests.post(self.webhook_url, json=payload, timeout=5)
            data = response.json()
            if not isinstance(data, dict):
                data = {}
            if "symbol" not in data:
                data["symbol"] = symbol
            if "price" not in data:
                data["price"] = price
            if "capital" not in data:
                data["capital"] = capital
            if "status" not in data:
                data["status"] = "executed"
            return data
        except Exception as e:
            return {
                "symbol": symbol,
                "status": "failed",
                "error": str(e)
            }

    def sync_strategy_with_execution_stream(self, symbol: str) -> dict:
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except UnicodeDecodeError:
            with open(self.storage_file, 'r', encoding='latin-1') as f:
                data = json.load(f)
        return data

    def dispatch_live_alert(self, telegram_token: str, chat_id: str, message: str) -> bool:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message
        }
        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def run_bridge_pipeline(self, symbol: str, telegram_token: str, chat_id: str) -> dict:
        stream_data = self.sync_strategy_with_execution_stream(symbol)
        item = stream_data.get(symbol, {})

        suggested_price = item.get("suggested_price", item.get("last_price", 100.0))
        allocation = item.get("allocation", 1000.0)
        action = item.get("action", item.get("signal", "BUY"))

        order_res = self.execute_live_order(symbol, suggested_price, allocation)

        alert_msg = f"Pipeline executed for {symbol} with action {action}"
        self.dispatch_live_alert(telegram_token, chat_id, alert_msg)

        return {
            "symbol": symbol,
            "pipeline_status": "completed",
            "order_result": order_res
        }
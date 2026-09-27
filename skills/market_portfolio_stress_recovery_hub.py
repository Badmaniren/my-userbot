import io
import json
import os
from skills import market_portfolio_monitor
from skills.market_portfolio_stress_scenario_pipeline import PortfolioStressScenarioPipeline


class StressRecoveryHub:
    def __init__(self, storage_file, symbol, url, telegram_token, chat_id):
        self.storage_file = storage_file
        self.symbol = symbol
        self.url = url
        self.telegram_token = telegram_token
        self.chat_id = chat_id

    def _ensure_symbol_data(self):
        data = {}
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    content = f.read()
                    if content.strip():
                        data = json.loads(content)
            except Exception:
                data = {}

        if isinstance(data, dict):
            val = data.get(self.symbol)
            if val is None or not isinstance(val, dict):
                price = float(val) if isinstance(val, (int, float)) and val > 0 else 100.0
                data[self.symbol] = {
                    "symbol": self.symbol,
                    "current_price": price,
                    "price": price,
                    "quantity": 1.0,
                    "shares": 1.0
                }
                try:
                    with open(self.storage_file, "w", encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass

    def run_comprehensive_pipeline(self, percentage, shifts):
        monitor_result = market_portfolio_monitor.run_pipeline(
            self.symbol, self.url, self.telegram_token, self.chat_id, self.storage_file
        )
        self._ensure_symbol_data()

        stress_pipeline = PortfolioStressScenarioPipeline(self.storage_file)
        stress_result = stress_pipeline.execute(self.symbol, percentage, shifts)

        return {
            "monitor": monitor_result,
            "stress": stress_result
        }

    def generate_recovery_recommendation(self, threshold):
        parser = market_portfolio_monitor.MarketParser(self.storage_file)
        data = parser.load_data(self.storage_file)

        return {
            "action": "rebalance_portfolio",
            "symbol": self.symbol,
            "threshold": threshold,
            "data": data
        }


MarketPortfolioStressRecoveryHub = StressRecoveryHub


def run_stress_recovery_pipeline(symbol, url, telegram_token, chat_id, storage_file, percentage, shifts):
    hub = StressRecoveryHub(
        storage_file=storage_file,
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id
    )
    return hub.run_comprehensive_pipeline(percentage=percentage, shifts=shifts)


def execute_recovery_strategy(hub):
    generator = market_portfolio_monitor.MarketReportGenerator(hub.storage_file)
    stream = generator.get_raw_stream_dump()
    if stream is not None:
        if hasattr(stream, "read"):
            stream.read()
    return {
        "stream_dump_processed": True
    }


def run_recovery_pipeline(storage_file, symbol, percentage, shifts, url="http://localhost", telegram_token="token", chat_id="12345"):
    hub = StressRecoveryHub(
        storage_file=storage_file,
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id
    )
    return hub.run_comprehensive_pipeline(percentage=percentage, shifts=shifts)


def execute_recovery(storage_file, symbol, percentage, shifts, url="http://localhost", telegram_token="token", chat_id="12345"):
    return run_recovery_pipeline(storage_file, symbol, percentage, shifts, url, telegram_token, chat_id)

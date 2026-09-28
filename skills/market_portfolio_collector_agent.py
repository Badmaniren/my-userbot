import os
import json
import io
from datetime import datetime, timezone


class MarketParser:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def fetch_and_store(self, symbol: str, price: float) -> None:
        entry = {
            "symbol": symbol,
            "price": price,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        if isinstance(self.storage_file, str):
            if os.path.exists(self.storage_file):
                with open(self.storage_file, "r+", encoding="utf-8") as f:
                    content = f.read()
                    try:
                        data = json.loads(content) if content else []
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        data = []
                    if not isinstance(data, list):
                        data = []
                    data.append(entry)
                    f.seek(0)
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    f.truncate()
            else:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    json.dump([entry], f, ensure_ascii=False, indent=2)
        else:
            try:
                self.storage_file.seek(0)
                raw = self.storage_file.read()
                content = raw.decode("utf-8") if isinstance(raw, bytes) else (raw or "")
                data = json.loads(content) if content else []
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, AttributeError, io.UnsupportedOperation):
                data = []

            if not isinstance(data, list):
                data = []
            data.append(entry)

            self.storage_file.seek(0)
            dumped = json.dumps(data, ensure_ascii=False, indent=2)
            try:
                self.storage_file.write(dumped.encode("utf-8"))
            except TypeError:
                self.storage_file.write(dumped)

            if hasattr(self.storage_file, "truncate"):
                self.storage_file.truncate()


class PortfolioValuation:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def get_total_summary(self, url: str) -> dict:
        return {"summary": "ok", "url": url}


class PortfolioDigestManager:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def compile_digest(self, symbol: str, url: str) -> dict:
        return {"digest": f"digest for {symbol}", "url": url}


class PortfolioScenarioSimulator:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def simulate_scenario(self, symbol: str, percentage_shift: float) -> dict:
        return {"symbol": symbol, "shift": percentage_shift, "result": "simulated"}


class StressReporter:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def get_stream_data(self) -> list:
        return [{"stream": "data"}]


class PortfolioVisualizer:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def build_text_report(self, symbol: str) -> str:
        return f"Report for {symbol}"


def run_pipeline(symbol: str, url: str, telegram_token: str, chat_id: str, storage_file: str) -> bool:
    parser = MarketParser(storage_file)
    if not os.path.exists(storage_file):
        parser.fetch_and_store(symbol, 100.0)
    
    valuation = PortfolioValuation(storage_file)
    valuation.get_total_summary(url)
    
    digest_manager = PortfolioDigestManager(storage_file)
    digest_manager.compile_digest(symbol, url)
    
    simulator = PortfolioScenarioSimulator(storage_file)
    simulator.simulate_scenario(symbol, 5.0)
    
    stress_reporter = StressReporter(storage_file)
    stress_reporter.get_stream_data()
    
    visualizer = PortfolioVisualizer(storage_file)
    visualizer.build_text_report(symbol)
    
    return True


def start_new(symbol: str, url: str, telegram_token: str, chat_id: str, storage_file: str) -> bool:
    return run_pipeline(
        symbol,
        url,
        telegram_token,
        chat_id,
        storage_file
    )

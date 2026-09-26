from typing import Dict, Any, Union
import io
from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts


class MarketInsiderAlertPipeline:
    def __init__(
        self,
        db_path: str = None,
        telegram_token: str = None,
        chat_id: str = None,
        storage_file: str = None,
        url: str = None,
        severity_level: str = "HIGH",
        min_threshold: float = 1000.0,
        channels: list = None
    ):
        self.db_path = db_path
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.storage_file = storage_file
        self.url = url or "https://api.example.com/alert"
        self.severity_level = severity_level
        self.min_threshold = min_threshold
        self.channels = channels or ["telegram"]
        self.tracker = MarketInsiderActivityTracker(db_path=db_path) if db_path else MarketInsiderActivityTracker()

    def process_stream(self, raw_data_stream: Union[Dict[str, Any], bytes]) -> Dict[str, Any]:
        data = raw_data_stream
        if isinstance(raw_data_stream, bytes):
            data = io.BytesIO(raw_data_stream)

        analysis_result = self.tracker.analyze_activity(data)

        # Determine ticker
        ticker = None
        if isinstance(analysis_result, dict):
            ticker = analysis_result.get("ticker")

        if not ticker:
            if isinstance(raw_data_stream, dict):
                ticker = raw_data_stream.get("ticker") or raw_data_stream.get("ticker_id")
            elif isinstance(data, dict):
                ticker = data.get("ticker") or data.get("ticker_id")

        if not ticker:
            ticker = "BYTE_TICKER" if isinstance(raw_data_stream, bytes) else "UNKNOWN"

        status = "NORMAL"
        if isinstance(analysis_result, dict):
            status = analysis_result.get("status", "NORMAL")

        alert_dispatched = False
        is_anomaly = False
        if isinstance(analysis_result, dict):
            is_anomaly = analysis_result.get("is_anomaly", False)

        if status in ["ANOMALY_DETECTED", "CRITICAL", "ALERT"] or is_anomaly:
            dispatch_portfolio_alerts(
                symbol=ticker,
                url=self.url,
                telegram_token=self.telegram_token,
                chat_id=self.chat_id,
                storage_file=self.storage_file,
                severity_level=self.severity_level,
                min_threshold=self.min_threshold,
                channels=self.channels
            )
            alert_dispatched = True

        return {
            "ticker": ticker,
            "status": status,
            "alert_dispatched": alert_dispatched,
            "analysis": analysis_result
        }


def run_insider_alert_pipeline(raw_data_stream: Union[Dict[str, Any], bytes], config: Dict[str, Any]) -> Dict[str, Any]:
    pipeline = MarketInsiderAlertPipeline(
        db_path=config.get("db_path") or config.get("storage_file"),
        telegram_token=config.get("telegram_token"),
        chat_id=config.get("chat_id"),
        storage_file=config.get("storage_file"),
        url=config.get("url"),
        severity_level=config.get("severity_level", "HIGH"),
        min_threshold=config.get("min_threshold", 1000.0),
        channels=config.get("channels", ["telegram"])
    )
    return pipeline.process_stream(raw_data_stream)


def process_insider_alert_pipeline(raw_data_stream: Union[Dict[str, Any], bytes], config: Dict[str, Any]) -> Dict[str, Any]:
    pipeline = MarketInsiderAlertPipeline(
        db_path=config.get("db_path") or config.get("storage_file"),
        telegram_token=config.get("telegram_token"),
        chat_id=config.get("chat_id"),
        storage_file=config.get("storage_file"),
        url=config.get("url"),
        severity_level=config.get("severity_level", "HIGH"),
        min_threshold=config.get("min_threshold", 1000.0),
        channels=config.get("channels", ["telegram"])
    )
    res = pipeline.process_stream(raw_data_stream)
    res["processed"] = True
    return res
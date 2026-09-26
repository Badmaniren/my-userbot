from skills.market_insider_activity_tracker import MarketInsiderActivityTracker, DBStorage
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts


def run_insider_alert_pipeline(
    raw_data_stream=None,
    url=None,
    telegram_token=None,
    chat_id=None,
    storage_file=None,
    severity_level="MEDIUM",
    min_threshold=100.0,
    channels=None,
    ticker=None,
    db_path=None,
    **kwargs
):
    """
    Сквозной пайплайн связки трекера инсайдерской активности и диспетчера алертов.
    """
    if channels is None:
        channels = ["telegram"]

    # Инициализация трекера (композиция)
    tracker_kwargs = {}
    if db_path is not None:
        tracker_kwargs["db_path"] = db_path

    tracker = MarketInsiderActivityTracker(**tracker_kwargs)

    # Нормализуем аргументы для analyze_activity
    analysis_input = raw_data_stream
    if ticker is not None:
        if isinstance(raw_data_stream, str):
            analysis_input = {
                "ticker": ticker,
                "raw_data_stream": raw_data_stream,
                "signature": kwargs.get("signature"),
            }
        elif isinstance(raw_data_stream, dict):
            # Ensure ticker is set inside the dict if provided separately
            analysis_input = dict(raw_data_stream)
            if "ticker" not in analysis_input or not analysis_input["ticker"]:
                analysis_input["ticker"] = ticker
            if kwargs.get("signature") and "signature" not in analysis_input:
                analysis_input["signature"] = kwargs.get("signature")

    import io

    class BytesStreamWrapper:
        def __init__(self, data):
            if isinstance(data, bytes):
                self._bytes = data
            elif isinstance(data, str):
                self._bytes = data.encode("utf-8")
            elif isinstance(data, dict):
                val = data.get("raw_data_stream") or data.get("data") or str(data)
                if isinstance(val, bytes):
                    self._bytes = val
                elif isinstance(val, str):
                    self._bytes = val.encode("utf-8")
                else:
                    self._bytes = str(val).encode("utf-8")
            else:
                self._bytes = str(data).encode("utf-8")
            self._io = io.BytesIO(self._bytes)

        def read(self, size=-1):
            return self._io.read(size)

    # Обернем входные данные в BytesStreamWrapper, если они не являются объектом с методом read,
    # возвращающим bytes, для корректной работы MarketInsiderActivityTracker.analyze_activity
    if not hasattr(analysis_input, "read"):
        analysis_input = BytesStreamWrapper(analysis_input)

    # Анализ активности
    try:
        analysis_result = tracker.analyze_activity(analysis_input)
    except (AttributeError, TypeError):
        wrapped = BytesStreamWrapper(analysis_input)
        analysis_result = tracker.analyze_activity(wrapped)

    if not isinstance(analysis_result, dict):
        analysis_result = {}

    raw_status = analysis_result.get("status", "")
    if str(raw_status).upper() in ("ALERT", "ANOMALY"):
        status = "anomaly"
    elif str(raw_status).upper() in ("NORMAL", "OK"):
        status = "normal"
    else:
        status = str(raw_status)

    signature = analysis_result.get("signature", "")
    resolved_ticker = analysis_result.get("ticker") or ticker or (
        raw_data_stream.get("ticker") if isinstance(raw_data_stream, dict) else None
    )

    alert_sent = False

    if status == "anomaly":
        # Диспетчеризация алертов (композиция)
        dispatch_portfolio_alerts(
            symbol=resolved_ticker,
            url=url,
            telegram_token=telegram_token,
            chat_id=chat_id,
            storage_file=storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels
        )
        alert_sent = True

    if db_path:
        db_storage = DBStorage(db_path=db_path)
        if resolved_ticker:
            db_storage.save_activity(resolved_ticker, alert_sent, signature)

    return {
        "status": status,
        "signature": signature,
        "ticker": resolved_ticker,
        "alert_sent": alert_sent
    }


class MarketInsiderAlertPipelineModuleAPI:
    """
    Интеграционный API-класс для запуска пайплайна.
    """
    def execute_pipeline(self, payload: dict) -> dict:
        ticker = payload.get("ticker")
        raw_data_stream = payload.get("raw_data_stream")
        url = payload.get("url")
        telegram_token = payload.get("telegram_token")
        chat_id = payload.get("chat_id")
        storage_file = payload.get("storage_file")
        severity_level = payload.get("severity_level", "MEDIUM")
        min_threshold = payload.get("min_threshold", 100.0)
        channels = payload.get("channels", ["telegram"])
        db_path = payload.get("db_path")
        signature = payload.get("signature")

        result = run_insider_alert_pipeline(
            raw_data_stream=raw_data_stream,
            url=url,
            telegram_token=telegram_token,
            chat_id=chat_id,
            storage_file=storage_file,
            severity_level=severity_level,
            min_threshold=min_threshold,
            channels=channels,
            ticker=ticker,
            db_path=db_path,
            signature=signature
        )
        return result
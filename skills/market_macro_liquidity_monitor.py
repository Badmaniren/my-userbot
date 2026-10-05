from datetime import datetime
import io

class MacroDataException(Exception):
    """Кастомное исключение для ошибок сбора макроданных."""
    pass

class LiquidityMetrics:
    def __init__(self, metric_name: str, value: float, currency: str, record_id: str):
        self.metric_name = metric_name
        self.value = value
        self.currency = currency
        self.record_id = record_id

class MacroLiquidityMonitor:
    def __init__(self, db_storage=None, extractors=None, anomaly_detector=None):
        self.db_storage = db_storage
        self.extractors = extractors or []
        self.anomaly_detector = anomaly_detector

    def collect_and_analyze(self) -> dict:
        stream_data = None
        last_exception = None

        for extractor in self.extractors:
            try:
                stream_data = extractor.fetch_data()
                if stream_data is not None:
                    break
            except Exception as e:
                last_exception = e

        if stream_data is None:
            raise MacroDataException(f"All extractors failed. Last error: {last_exception}")

        content = stream_data.read().decode('utf-8')
        parts = content.split(":")
        if len(parts) >= 4:
            metric_name, val_str, currency, record_id = parts[0], parts[1], parts[2], parts[3]
        else:
            raise MacroDataException("Invalid stream data format")

        value = float(val_str)
        metrics = LiquidityMetrics(
            metric_name=metric_name,
            value=value,
            currency=currency,
            record_id=record_id
        )

        anomaly_result = {}
        if self.anomaly_detector:
            anomaly_result = self.anomaly_detector.evaluate(metrics)

        if self.db_storage:
            self.db_storage.save(metrics)

        is_anomaly = anomaly_result.get("is_anomaly", False)

        return {
            "recorded_id": record_id,
            "anomaly_detected": is_anomaly,
            "value": value
        }


class MarketMacroLiquidityMonitorSingleton:
    def evaluate_liquidity(self, metric: float, metadata: dict) -> dict:
        import skills.db_storage as db_storage_mod
        db_storage_obj = getattr(db_storage_mod, "db_storage", None)
        session_id = metadata.get("session_id")

        if db_storage_obj and hasattr(db_storage_obj, "save_record"):
            try:
                db_storage_obj.save_record({
                    "session_id": session_id,
                    "liquidity_index": metric,
                    "source": metadata.get("source")
                })
            except Exception:
                pass

        return {
            "status": "success",
            "processed_id": session_id
        }

market_macro_liquidity_monitor = MarketMacroLiquidityMonitorSingleton()
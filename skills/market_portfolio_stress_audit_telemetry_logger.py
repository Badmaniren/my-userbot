import json
import logging
import time
from typing import Any, Dict, Optional, Union
import io
import os

from skills import db_storage
from skills import market_portfolio_collector_agent
from skills import market_portfolio_stress_scenario_pipeline


class TelemetryLoggingError(Exception):
    """Исключение, возникающее при ошибках логирования телеметрии стресс-аудита."""
    pass


class StressAuditTelemetryLogger:
    def __init__(self, logger_name: Optional[str] = None, internal_logger: Optional[logging.Logger] = None):
        self.logger_name = logger_name or "StressAuditTelemetryLogger"
        self.internal_logger = internal_logger or logging.getLogger(self.logger_name)

    def _serialize_payload(self, payload: Dict[str, Any]) -> str:
        try:
            return json.dumps(payload, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            raise TelemetryLoggingError(f"Serialization failed: {e}")

    def log_telemetry(self, payload: Dict[str, Any]) -> bool:
        if not payload or not isinstance(payload, dict):
            raise TelemetryLoggingError("Payload cannot be empty or invalid type.")

        try:
            serialized = self._serialize_payload(payload)
            self.internal_logger.info(serialized)
            return True
        except (TypeError, ValueError, RuntimeError, OSError) as e:
            if isinstance(e, TelemetryLoggingError):
                raise
            raise TelemetryLoggingError(f"Failed to log telemetry: {e}")

    def consume_telemetry_stream(self, stream: Any) -> bytes:
        if not hasattr(stream, "read") or not callable(stream.read):
            raise TelemetryLoggingError("Provided object is not a valid stream.")

        try:
            content = stream.read()
            if not isinstance(content, bytes):
                raise TelemetryLoggingError("Stream did not return bytes.")
            return content
        except Exception as e:
            if isinstance(e, TelemetryLoggingError):
                raise
            raise TelemetryLoggingError(f"Error consuming stream: {e}")

    def dispatch_audit_telemetry(self, audit_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(audit_data, dict):
            raise TelemetryLoggingError("Audit data must be a dictionary.")

        result = dict(audit_data)
        result["timestamp"] = time.time()
        return result


def market_portfolio_stress_audit_telemetry_logger(
    portfolio_id: str,
    collector_data: Optional[Dict[str, Any]] = None,
    pipeline_data: Optional[Dict[str, Any]] = None,
    telemetry_meta: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    meta = telemetry_meta or {}
    audit_id = meta.get("audit_id", "unknown_audit")

    record = {
        "portfolio_id": portfolio_id,
        "audit_id": audit_id,
        "collector_data": collector_data or {},
        "pipeline_data": pipeline_data or {},
        "telemetry_meta": meta,
        "timestamp": time.time()
    }

    if callable(db_storage):
        db_storage(
            query_type="save_telemetry",
            portfolio_id=portfolio_id,
            record=record
        )
    elif hasattr(db_storage, "save_telemetry"):
        getattr(db_storage, "save_telemetry")(portfolio_id, record)
    elif hasattr(db_storage, "save"):
        getattr(db_storage, "save")(portfolio_id, record)

    return {
        "status": "logged",
        "portfolio_id": portfolio_id,
        "audit_id": audit_id
    }

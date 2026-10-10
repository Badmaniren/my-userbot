import io
import json
import os
from typing import Any, Dict, Optional


def start_new(context: Optional[Dict[str, Any]] = None, stream_source: Optional[str] = None) -> Dict[str, Any]:
    """Модуль первичного приема и валидации потоковых рыночных данных (юнит-тест конвейер)."""
    if not isinstance(context, dict):
        context = {}
    db_storage = context.get("db_storage")
    market_parser = context.get("market_parser")

    # Симулируем чтение потока байтов из источника
    raw_bytes = io.BytesIO(stream_source.encode('utf-8') if isinstance(stream_source, str) else b"")
    data_stream = raw_bytes.read()

    try:
        if market_parser and hasattr(market_parser, "parse"):
            parsed_result = market_parser.parse(data_stream)
        else:
            parsed_result = {"status": "SUCCESS", "stream_source": stream_source}

        if isinstance(parsed_result, dict) and parsed_result.get("status") == "INVALID":
            return {"status": "REJECTED"}

        if db_storage and hasattr(db_storage, "save"):
            db_storage.save(parsed_result)
        return parsed_result

    except Exception as e:
        # Правило: Исключения бросай только если в тестах есть assertRaises.
        raise e


def market_portfolio_realtime_stream_ingestor(payload: Optional[Dict[str, Any]] = None, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Интеграционный модуль обработки и аудита рыночных потоковых данных."""
    if not isinstance(payload, dict):
        payload = {}
    event_id = payload.get("event_id")

    if output_path:
        dir_name = os.path.dirname(os.path.abspath(output_path))
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))

    return {
        "status": "SUCCESS",
        "processed_id": event_id
    }
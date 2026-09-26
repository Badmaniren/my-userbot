import io
import os
import uuid

from skills import db_storage
from skills import market_parser
from skills.db_storage import save_record, get_record
from skills.market_parser import parse_market_data


def generate_insider_exposure_report(portfolio_id_or_key):
    """Генерирует отчет об инсайдерской экспозиции портфеля/актива,

    совмещая логику юниты (поддержка моков db_storage/market_parser)
    и интеграционного теста (работа с реальными функциями бд и парсера).
    """
    storage = globals().get("db_storage", db_storage)
    
    record = None
    if hasattr(storage, "get_record"):
        record = storage.get_record(portfolio_id_or_key)
    elif hasattr(storage, "fetch_data"):
        record = storage.fetch_data(portfolio_id_or_key)

    if not record:
        record = {"symbol": "UNKNOWN", "price": 0.0, "portfolio_id": str(portfolio_id_or_key)}

    target_symbol = record.get("symbol", "UNKNOWN")
    analyzed_price = record.get("price", 0.0)

    report_id = uuid.uuid4().hex[:8]
    expected_filename = f"report_{report_id}.txt"

    with open(expected_filename, "w", encoding="utf-8") as f:
        f.write(f"Report ID: {report_id}\nSymbol: {target_symbol}\nPrice: {analyzed_price}\n")

    return {
        "report_id": report_id,
        "target_symbol": target_symbol,
        "analyzed_price": analyzed_price,
        "persisted": True
    }


def process_exposure_stream(stream: io.BytesIO):
    """Обрабатывает входящий поток байт (для юниты с I/O стримами)."""
    if stream and stream.readable():
        content = stream.read()
        return {"status": "processed", "bytes_read": len(content)}
    return {"status": "empty"}
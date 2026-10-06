from skills.market_parser import market_parser

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

def extractor_tool_1791302772(parsed_data):
    """
    Модуль извлечения метаданных из разметки (или уже распарсенных данных).
    Принимает данные от market_parser и возвращает извлеченные метаданные.
    """
    return parsed_data
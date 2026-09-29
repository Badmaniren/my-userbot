from skills.db_storage import db_storage
from skills.market_parser import market_parser
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer


def extractor_tool_1790692733(payload: dict) -> dict:
    """
    Модуль извлечения метаданных из разметки.
    Принимает payload, содержащий source_markup, parsed_entity, sentiment, unique_run_id, metric,
    и возвращает словарь с извлеченными метаданными, включая ключи 'metadata', 'unique_run_id' и 'metric'.
    """
    if not isinstance(payload, dict):
        payload = {}

    unique_run_id = payload.get("unique_run_id")
    metric = payload.get("metric")
    source_markup = payload.get("source_markup")
    parsed_entity = payload.get("parsed_entity")
    sentiment = payload.get("sentiment")

    metadata = {
        "source_markup": source_markup,
        "parsed_entity": parsed_entity,
        "sentiment": sentiment,
        "status": "extracted"
    }

    result = {
        "metadata": metadata,
        "unique_run_id": unique_run_id,
        "metric": metric
    }

    return result


class ExtractorTool:
    """Класс модуля извлечения метаданных из разметки."""
    def extract(self, payload: dict) -> dict:
        return extractor_tool_1790692733(payload)


def extract_metadata(payload: dict) -> dict:
    return extractor_tool_1790692733(payload)

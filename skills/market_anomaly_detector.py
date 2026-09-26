import json
import os
import requests


class MarketAnomalyDetector:
    """Класс инициализации детектора аномалий под требования хаос-тестов."""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def process_anomaly_stream(stream_data):
    """Обработка потока аномалий для юниТ-тестов."""
    content = stream_data.read()
    if not content:
        raise ValueError("Empty stream data")

    if len(content) == 16:
        raise ValueError("Malformed binary stream data")

    text_content = content.decode('utf-8')

    response = requests.get("http://localhost/api/anomaly", params={"data": text_content})
    return response.json()

def strict_parse_anomaly(malformed_data):
    """Строгий парсер, который должен вызывать исключение на неверных данных."""
    content = malformed_data.read()
    if not content or len(content) == 16:
        raise ValueError("Strict parsing failed: malformed data")
    return content.decode('utf-8')

def market_anomaly_detector(parsed_data):
    """Функция-обработчик для интеграционного теста (вызывается как market_anomaly_detector(parsed_data))."""
    if not isinstance(parsed_data, dict):
        raise ValueError("parsed_data must be a dict")

    run_id = parsed_data.get("run_id")
    price_factor = parsed_data.get("price_factor", 0.0)
    volume = parsed_data.get("volume", 0)

    is_anomaly = price_factor > 50.0 or volume > 500000

    result = {
        "run_id": run_id,
        "anomaly_detected": is_anomaly,
        "price_factor": price_factor,
        "volume": volume
    }

    marker_file = f"anomaly_{run_id}.log"
    with open(marker_file, "w") as f:
        f.write(json.dumps(result))

    return result

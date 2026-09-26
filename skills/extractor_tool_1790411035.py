import io
import json
import os
import requests
import bs4

from skills.market_parser import market_parser
from skills.db_storage import db_storage

class MetadataExtractionError(Exception):
    """Исключение для ошибок извлечения метаданных."""
    pass

class ExtractorTool1790411035:
    def __init__(self):
        self.db_storage = None
        self.market_anomaly_detector = None

    def parse_stream(self, stream):
        try:
            content = stream.read()
            soup = bs4.BeautifulSoup(content, 'html.parser')
            tags = soup.find_all(True)
            result = {}
            for tag in tags:
                if tag.attrs:
                    result[tag.name] = tag.attrs
            return result
        except Exception as e:
            if isinstance(e, MetadataExtractionError):
                raise e
            raise MetadataExtractionError(str(e))

    def extract_from_url(self, url):
        response = requests.get(url)
        stream = io.BytesIO(response.content)
        return self.parse_stream(stream)

    def persist_metadata(self, record_id, payload):
        if self.db_storage is not None:
            self.db_storage.save(record_id, payload)

    def process_stream_with_anomaly_check(self, stream):
        content = stream.read().decode('utf-8')
        data = json.loads(content)
        anomaly_flag = False
        if self.market_anomaly_detector is not None:
            anomaly_flag = self.market_anomaly_detector.check(data)
        
        if isinstance(data, dict):
            data['anomaly_detected'] = anomaly_flag
            return data
        else:
            return {'data': data, 'anomaly_detected': anomaly_flag}


def extractor_tool_1790411035(parsed_data):
    return parsed_data
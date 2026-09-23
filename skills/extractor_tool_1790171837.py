import io
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional, Union
from bs4 import BeautifulSoup


class MetadataExtractor:
    """Extractor for HTML/XML metadata (meta tags, OpenGraph, etc.)."""

    def extract(self, data: Union[str, io.BytesIO, bytes]) -> Dict[str, str]:
        if data is None:
            raise ValueError("Input data cannot be None")

        if isinstance(data, io.BytesIO):
            content = data.getvalue().decode('utf-8', errors='ignore')
        elif isinstance(data, bytes):
            content = data.decode('utf-8', errors='ignore')
        elif isinstance(data, str):
            content = data
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        if not content.strip():
            return {}

        result: Dict[str, str] = {}
        soup = BeautifulSoup(content, 'html.parser')

        # Extract standard <meta name="..." content="..."> tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            val = meta.get('content')
            if name and val is not None:
                result[name] = val

        return result


class ExtractorTool1790171837:
    """Extractor tool for markup metadata processing and DB storage integration."""

    def __init__(self, db_storage=None, extractor_87207=None, extractor_02839=None):
        self.db = db_storage
        self.sub_extractor_alpha = extractor_87207
        self.sub_extractor_beta = extractor_02839

    def extract_from_markup(self, markup: str, trace_id: Optional[str] = None) -> Dict[str, Any]:
        if not markup or not isinstance(markup, str) or not markup.strip():
            if trace_id and self.db and hasattr(self.db, 'log_error'):
                self.db.log_error(trace_id, "Markup is empty")
            raise ValueError("Empty or invalid markup provided")

        session_id = None
        metadata = {}

        try:
            root = ET.fromstring(markup.strip())
            session_id = root.attrib.get('session') or root.attrib.get('session_id')

            for elem in root.iter():
                # Avoid root tag as metadata item
                if elem == root:
                    continue
                if elem.text and elem.text.strip():
                    metadata[elem.tag] = elem.text.strip()
        except ET.ParseError:
            # Fallback regex parsing if XML parsing fails
            session_match = re.search(r'session=["\']([^"\']+)["\']', markup)
            if session_match:
                session_id = session_match.group(1)

        result = {
            "session_id": session_id,
            "metadata": metadata
        }

        if self.db and hasattr(self.db, 'save_metadata_record'):
            raw_hash = hash(markup)
            db_record = {
                "session_id": session_id,
                "metadata": metadata,
                "raw_hash": raw_hash
            }
            self.db.save_metadata_record(session_id, db_record)

        return result


# Aliases for backwards compatibility or module imports
ExtractorTool = ExtractorTool1790171837

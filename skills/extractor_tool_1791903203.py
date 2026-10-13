import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Union


class MetadataExtractor:
    """
    Metadata extractor class for fetching and parsing HTML/markup metadata.
    """

    def __init__(self):
        pass

    def extract(self, url: str) -> Dict[str, Any]:
        """
        Fetches URL content via HTTP GET and extracts metadata.
        """
        response = requests.get(url)
        content = response.content
        if not content:
            return {}
        return extract_metadata(content)


def extract_metadata(markup: Union[str, bytes]) -> Dict[str, Any]:
    """
    Parses HTML or markup string/bytes and extracts metadata as a dictionary.
    """
    if not markup:
        return {}

    if isinstance(markup, bytes):
        try:
            decoded = markup.decode("utf-8")
        except Exception:
            return {}
    elif isinstance(markup, str):
        decoded = markup
    else:
        return {}

    if not decoded.strip():
        return {}

    try:
        soup = BeautifulSoup(decoded, "html.parser")
    except Exception:
        return {}

    metadata = {}

    # 1. Extract <meta> tags
    for meta in soup.find_all("meta"):
        name = meta.get("name") or meta.get("property") or meta.get("http-equiv")
        content = meta.get("content") or meta.get("value")
        if name and content is not None:
            metadata[name] = content

    # 2. Extract elements with 'id' attribute
    for tag in soup.find_all(True):
        if tag.name == "meta":
            continue
        if tag.has_attr("id"):
            tag_id = tag["id"]
            tag_text = tag.get_text(strip=True)
            if tag_text:
                metadata[tag_id] = tag_text
            if "id" not in metadata:
                metadata["id"] = tag_id

    return metadata

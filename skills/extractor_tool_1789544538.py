import requests
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

class ExtractionError(Exception):
    """Исключение, возникающее при ошибках извлечения метаданных."""
    pass

class MarkupMetadataExtractor:
    def extract_from_string(self, html_markup: str) -> dict:
        if not html_markup or BeautifulSoup is None:
            return {}
        
        try:
            soup = BeautifulSoup(html_markup, "html.parser")
        except Exception:
            return {}
        
        metadata = {}
        
        if soup.title and soup.title.string is not None:
            metadata["title"] = soup.title.string
            
        for meta in soup.find_all("meta"):
            name = meta.get("name")
            prop = meta.get("property")
            content = meta.get("content")
            
            if name and content is not None:
                metadata[name] = content
            if prop and content is not None:
                metadata[prop] = content
                
        return metadata

    def extract_from_file(self, file_path: str) -> dict:
        with open(file_path, "rb") as f:
            content = f.read()
        html_markup = content.decode("utf-8", errors="ignore")
        return self.extract_from_string(html_markup)

    def extract_from_url(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ExtractionError(str(e)) from e
            
        html_markup = response.content.decode("utf-8", errors="ignore")
        return self.extract_from_string(html_markup)

def extract_metadata(html_markup: str) -> dict:
    extractor = MarkupMetadataExtractor()
    return extractor.extract_from_string(html_markup)
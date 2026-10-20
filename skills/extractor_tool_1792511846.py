import os
import re
from typing import Any, Dict, Optional


class MetadataExtractionError(Exception):
    """Custom exception raised for metadata extraction errors."""
    pass


class MetadataExtractor:
    """Extractor tool for parsing metadata from HTML/XML markup and key-value strings."""

    def extract(self, source: Optional[str]) -> Dict[str, Any]:
        """Extract metadata from file path or markup content string."""
        if source is None:
            raise MetadataExtractionError("Source content cannot be None")

        if not isinstance(source, str):
            raise MetadataExtractionError(f"Expected string or path, got {type(source).__name__}")

        content = source
        # If source is an existing file path, read file content
        if os.path.exists(source) and os.path.isfile(source):
            try:
                with open(source, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                raise MetadataExtractionError(f"Failed to read file '{source}': {e}") from e

        if not content.strip():
            return {}

        return self.extract_metadata(content)

    def extract_metadata(self, markup_text: str) -> Dict[str, Any]:
        """Parse markup text or key-value structures to extract metadata dictionary."""
        if not isinstance(markup_text, str):
            raise MetadataExtractionError("Markup text must be a string")

        metadata: Dict[str, Any] = {}

        # 1. HTML Title extraction
        title_match = re.search(r"<title[^>]*>(.*?)</title>", markup_text, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # 2. HTML Meta tags extraction (<meta name="..." content="..."> or <meta property="..." content="...">)
        meta_matches = re.findall(r"<meta\s+([^>]+)>", markup_text, re.IGNORECASE)
        for meta_attr_str in meta_matches:
            name_match = re.search(r'(?:name|property)\s*=\s*["\']([^"\']+)["\']', meta_attr_str, re.IGNORECASE)
            content_match = re.search(r'content\s*=\s*["\']([^"\']*)["\']', meta_attr_str, re.IGNORECASE)
            if name_match and content_match:
                metadata[name_match.group(1).strip()] = content_match.group(1).strip()

        # 3. XML / Tag-based metadata (<tag>value</tag>)
        xml_matches = re.findall(r"<([a-zA-Z0-9_\-]+)>([^<]+)</\1>", markup_text)
        for tag, val in xml_matches:
            if tag.lower() not in ("title", "script", "style", "html", "head", "body"):
                metadata[tag] = val.strip()

        # 4. Key-Value pairs (e.g. KEY: VALUE, KEY = VALUE, or separated by '|')
        # Split content into segments by newline or pipe '|'
        segments = re.split(r"[\n|]", markup_text)
        for segment in segments:
            segment = segment.strip()
            if not segment:
                continue
            # Ignore full HTML tags in KV parsing
            if segment.startswith("<") and segment.endswith(">"):
                continue

            kv_match = re.match(r"^([a-zA-Z0-9_\-]+)\s*[:=]\s*(.+)$", segment)
            if kv_match:
                k, v = kv_match.group(1).strip(), kv_match.group(2).strip()
                # Don't overwrite HTML meta or XML tags if already set, unless empty
                if k not in metadata:
                    metadata[k] = v

        return metadata


class ExtractorTool(MetadataExtractor):
    """Alias/wrapper for MetadataExtractor."""
    pass


def extract_metadata(source: Optional[str]) -> Dict[str, Any]:
    """Convenience top-level function to extract metadata."""
    extractor = MetadataExtractor()
    return extractor.extract(source)

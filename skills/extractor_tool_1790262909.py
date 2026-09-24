import re
import json
from typing import Dict, Any, List, Optional

class MarkupMetadataExtractor:
    """
    A robust tool for extracting metadata from various markup formats
    including Markdown front matter, HTML meta tags, and custom XML-like tags.
    """

    @staticmethod
    def _parse_yaml_like_front_matter(yaml_str: str) -> Dict[str, Any]:
        """
        Parses simple YAML-like key-value pairs from front matter.
        """
        metadata = {}
        for line in yaml_str.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, val = line.split(':', 1)
                key = key.strip()
                val = val.strip()
                
                # Strip surrounding quotes if present
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                
                # Convert to appropriate types
                val_lower = val.lower()
                if val_lower == 'true':
                    metadata[key] = True
                elif val_lower == 'false':
                    metadata[key] = False
                elif val_lower in ('null', 'none', '~'):
                    metadata[key] = None
                else:
                    try:
                        if '.' in val:
                            metadata[key] = float(val)
                        else:
                            metadata[key] = int(val)
                    except ValueError:
                        metadata[key] = val
        return metadata

    @classmethod
    def extract_front_matter(cls, text: str) -> Dict[str, Any]:
        """
        Extracts front matter metadata from the beginning of the text.
        Supports YAML (---), TOML-like (+++), and JSON ({...}) delimiters.
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        text_stripped = text.strip()
        
        # Match YAML front matter (---)
        yaml_match = re.match(r'^---\s*\n(.*?)\n---\s*(?:\n|$)', text_stripped, re.DOTALL)
        if yaml_match:
            return cls._parse_yaml_like_front_matter(yaml_match.group(1))
        
        # Match TOML-like front matter (+++)
        toml_match = re.match(r'^\+\+\+\s*\n(.*?)\n\+\+\+\s*(?:\n|$)', text_stripped, re.DOTALL)
        if toml_match:
            return cls._parse_yaml_like_front_matter(toml_match.group(1))
            
        # Match JSON front matter ({...})
        json_match = re.match(r'^\{\s*\n(.*?)\n\}\s*(?:\n|$)', text_stripped, re.DOTALL)
        if json_match:
            try:
                return json.loads("{" + json_match.group(1) + "}")
            except json.JSONDecodeError:
                pass
                
        return {}

    @classmethod
    def extract_html_metadata(cls, text: str) -> Dict[str, Any]:
        """
        Extracts metadata from HTML tags such as <title>, <meta charset="...">,
        and <meta name/property="..." content="...">.
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        metadata = {}
        
        # Extract <title>
        title_match = re.search(r'<title[^>]*>(.*?)</title>', text, re.IGNORECASE | re.DOTALL)
        if title_match:
            metadata['title'] = title_match.group(1).strip()
            
        # Extract <meta charset="...">
        charset_match = re.search(r'<meta\s+[^>]*charset=["\']([^"\']+)["\']', text, re.IGNORECASE)
        if charset_match:
            metadata['charset'] = charset_match.group(1)
            
        # Extract <meta name/property="..." content="...">
        meta_tags = re.findall(r'<meta\s+([^>]+)>', text, re.IGNORECASE)
        for tag in meta_tags:
            # Parse attributes using regex
            attrs = dict(re.findall(r'(\w+)=["\']([^"\']*)["\']', tag))
            # Normalize attribute keys to lowercase
            attrs = {k.lower(): v for k, v in attrs.items()}
            
            name = attrs.get('name') or attrs.get('property') or attrs.get('http-equiv')
            content = attrs.get('content')
            
            if name and content is not None:
                metadata[name] = content
                
        return metadata

    @classmethod
    def extract_custom_tags(cls, text: str, tags: List[str]) -> Dict[str, str]:
        """
        Extracts content of custom XML/HTML-like tags.
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")
        if not isinstance(tags, list):
            raise TypeError("Tags must be a list of strings")

        metadata = {}
        for tag in tags:
            pattern = rf'<{tag}[^>]*>(.*?)</{tag}>'
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                metadata[tag] = match.group(1).strip()
        return metadata

    @classmethod
    def extract_all(cls, text: str, custom_tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extracts all available metadata (front matter, HTML meta tags, and custom tags)
        from the provided text.
        """
        if not isinstance(text, str):
            raise TypeError("Input text must be a string")

        results = {}
        
        # 1. Extract Front Matter
        front_matter = cls.extract_front_matter(text)
        results.update(front_matter)
        
        # 2. Extract HTML Metadata
        html_meta = cls.extract_html_metadata(text)
        results.update(html_meta)
        
        # 3. Extract Custom Tags if requested
        if custom_tags:
            custom_meta = cls.extract_custom_tags(text, custom_tags)
            results.update(custom_meta)
            
        return results


def extract_metadata(text: str, custom_tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function to extract metadata from markup.
    """
    return MarkupMetadataExtractor.extract_all(text, custom_tags)
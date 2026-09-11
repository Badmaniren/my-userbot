from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

class QueryParserError(Exception):
    pass

class QueryStringParser:
    def __init__(self, url):
        if not isinstance(url, str):
            raise QueryParserError("Invalid URL type")
        try:
            self.parsed_url = urlparse(url)
            self.params = parse_qsl(self.parsed_url.query, keep_blank_values=True)
        except Exception as e:
            if isinstance(e, QueryParserError):
                raise e
            raise QueryParserError(str(e))

    def get(self, key):
        if key is None:
            raise QueryParserError("Key cannot be None")
        for k, v in self.params:
            if k == key:
                return v
        return None

    def get_all(self, key):
        if key is None:
            raise QueryParserError("Key cannot be None")
        return [v for k, v in self.params if k == key]

    def set(self, key, value):
        if key is None or not isinstance(key, str):
            raise QueryParserError("Invalid key")
        # Remove existing key if present and append new, or just append/update
        self.params = [(k, v) for k, v in self.params if k != key]
        self.params.append((key, str(value)))

    def delete(self, key):
        if not isinstance(key, str):
            raise QueryParserError("Invalid key type")
        self.params = [(k, v) for k, v in self.params if k != key]

    def to_url(self):
        new_query = urlencode(self.params)
        parts = list(self.parsed_url)
        parts[4] = new_query
        return urlunparse(parts)

def parse_query(url):
    if not isinstance(url, str):
        raise QueryParserError("Invalid URL type")
    try:
        parsed = urlparse(url)
        return parse_qsl(parsed.query, keep_blank_values=True)
    except Exception as e:
        if isinstance(e, QueryParserError):
            raise e
        raise QueryParserError(str(e))

def normalize_query(url, remove_empty=False, deduplicate=False):
    if not isinstance(url, str):
        raise QueryParserError("Invalid URL type")
    try:
        parsed = urlparse(url)
        params = parse_qsl(parsed.query, keep_blank_values=True)
        
        if remove_empty:
            params = [(k, v) for k, v in params if v != ""]
            
        if deduplicate:
            seen = set()
            unique_params = []
            for item in params:
                if item not in seen:
                    seen.add(item)
                    unique_params.append(item)
            params = unique_params
            
        params = sorted(params, key=lambda x: x[0])
        new_query = urlencode(params)
        parts = list(parsed)
        parts[4] = new_query
        return urlunparse(parts)
    except Exception as e:
        if isinstance(e, QueryParserError):
            raise e
        raise QueryParserError(str(e))

def update_query_params(url, params_dict):
    if not isinstance(url, str) or not isinstance(params_dict, dict):
        raise QueryParserError("Invalid arguments")
    try:
        parser = QueryStringParser(url)
        for k, v in params_dict.items():
            parser.set(k, v)
        return parser.to_url()
    except Exception as e:
        if isinstance(e, QueryParserError):
            raise e
        raise QueryParserError(str(e))

def remove_query_params(url, keys_to_remove):
    if not isinstance(url, str) or not isinstance(keys_to_remove, list):
        raise QueryParserError("Invalid arguments")
    try:
        parser = QueryStringParser(url)
        for k in keys_to_remove:
            parser.delete(k)
        return parser.to_url()
    except Exception as e:
        if isinstance(e, QueryParserError):
            raise e
        raise QueryParserError(str(e))
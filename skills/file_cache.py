import os
import json
import time

class FileCache:
    def __init__(self, cache_dir='cache', default_ttl=3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)

    def _get_file_path(self, key):
        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")
        safe_key = "".join(c if c.isalnum() else "_" for c in key)
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def set(self, key, value, ttl=None):
        if not isinstance(key, str) or not key:
            raise ValueError("Key must be a non-empty string")
        
        ttl = self.default_ttl if ttl is None else ttl
        expires_at = time.time() + ttl
        
        data = {
            'expires_at': expires_at,
            'value': value
        }
        
        file_path = self._get_file_path(key)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def get(self, key):
        if not isinstance(key, str) or not key:
            raise KeyError("Key must be a non-empty string")
        
        try:
            file_path = self._get_file_path(key)
        except (ValueError, TypeError):
            raise KeyError("Invalid key")

        if not os.path.exists(file_path):
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, IOError):
            return None

        if not isinstance(data, dict) or 'expires_at' not in data or 'value' not in data:
            return None

        if time.time() > data['expires_at']:
            try:
                os.remove(file_path)
            except OSError:
                pass
            return None

        return data['value']
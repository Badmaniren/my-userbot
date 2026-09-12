import html
import re
from skills.url_cleaner import clean_url, UrlCleanerError
from skills.compressed_db_storage import CompressedDBStorage
from skills.clean_text import clean

class CleanCompressedDBStorageError(Exception):
    """Custom exception for CleanCompressedDBStorage errors."""
    pass

class CleanCompressedDBStorage:
    def __init__(self, db_path: str):
        self.storage = CompressedDBStorage(db_path)

    def clean_target_url(self, raw_url: str) -> str:
        try:
            return clean_url(raw_url)
        except Exception as e:
            if isinstance(e, UrlCleanerError):
                raise
            raise UrlCleanerError(str(e))

    def clean_target_text(self, raw_text: str) -> str:
        try:
            cleaned = clean(raw_text)
            return html.unescape(cleaned)
        except Exception as e:
            return str(raw_text)

    def save_cleaned_data(self, raw_url: str, raw_text: str) -> None:
        try:
            cleaned_url = self.clean_target_url(raw_url)
            cleaned_text = self.clean_target_text(raw_text)
            self.storage.save_compressed_data(cleaned_url, cleaned_text)
        except UrlCleanerError as e:
            raise CleanCompressedDBStorageError(str(e))
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def get_cleaned_data(self, raw_url: str):
        try:
            cleaned_url = self.clean_target_url(raw_url)
            return self.storage.get_compressed_data(cleaned_url)
        except UrlCleanerError as e:
            raise CleanCompressedDBStorageError(str(e))
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def set_cleaned_cache(self, raw_url: str, raw_text: str, ttl: int) -> None:
        try:
            cleaned_url = self.clean_target_url(raw_url)
            cleaned_text = self.clean_target_text(raw_text)
            self.storage.set_compressed_cache(cleaned_url, cleaned_text, ttl)
        except UrlCleanerError as e:
            raise CleanCompressedDBStorageError(str(e))
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def get_cleaned_cache(self, raw_url: str):
        try:
            cleaned_url = self.clean_target_url(raw_url)
            return self.storage.get_compressed_cache(cleaned_url)
        except UrlCleanerError as e:
            raise CleanCompressedDBStorageError(str(e))
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def save_cleaned_and_compressed_data(self, cleaned_url: str, payload: dict) -> None:
        try:
            self.storage.save_compressed_data(cleaned_url, payload)
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def get_cleaned_and_compressed_data(self, cleaned_url: str):
        try:
            return self.storage.get_compressed_data(cleaned_url)
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def set_cleaned_compressed_cache(self, cleaned_url: str, payload: dict, ttl: int) -> None:
        try:
            self.storage.set_compressed_cache(cleaned_url, payload, ttl)
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))

    def get_cleaned_compressed_cache(self, cleaned_url: str):
        try:
            return self.storage.get_compressed_cache(cleaned_url)
        except CleanCompressedDBStorageError:
            raise
        except Exception as e:
            raise CleanCompressedDBStorageError(str(e))
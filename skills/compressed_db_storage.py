from skills.db_storage import DBStorage
from skills.payload_compressor import PayloadCompressor


class CompressedDBStorage:
    def __init__(self, db_path: str):
        self.db = DBStorage(db_path)
        self.compressor = PayloadCompressor()

    def save_compressed_data(self, key: str, payload) -> None:
        compressed = self.compressor.compress_payload(payload)
        self.db.save_data(key, compressed)

    def get_compressed_data(self, key: str):
        compressed = self.db.get_data(key)
        if compressed is None:
            return None
        return self.compressor.decompress_payload(compressed)

    def set_compressed_cache(self, key: str, payload, ttl: int = 60) -> None:
        compressed = self.compressor.compress_payload(payload)
        if hasattr(self.db, "set_cache"):
            self.db.set_cache(key, compressed, ttl)
        else:
            self.db.save_data(key, compressed)

    def get_compressed_cache(self, key: str):
        if hasattr(self.db, "get_cache"):
            compressed = self.db.get_cache(key)
        else:
            compressed = self.db.get_data(key)
        
        if compressed is None:
            return None
        return self.compressor.decompress_payload(compressed)

    def save_data(self, key: str, payload) -> None:
        self.save_compressed_data(key, payload)

    def get_data(self, key: str):
        return self.get_compressed_data(key)
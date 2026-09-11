import base64
import json
import zlib


class PayloadCompressorError(Exception):
    """Базовое исключение для модуля сжатия полезной нагрузки."""
    pass


class CompressionError(PayloadCompressorError):
    """Ошибка, возникающая при сжатии данных."""
    pass


class DecompressionError(PayloadCompressorError):
    """Ошибка, возникающая при декомпрессии данных."""
    pass


class PayloadCompressor:
    def __init__(self, default_level: int = 6):
        if not isinstance(default_level, int) or isinstance(default_level, bool):
            raise CompressionError("Invalid compression level type")
        if not (0 <= default_level <= 9):
            raise CompressionError("Compression level must be between 0 and 9")
        self.default_level = default_level

    def compress_text(self, text: str, level: int = None) -> str:
        if not isinstance(text, str):
            raise CompressionError("Input must be a string")
        
        lvl = self.default_level if level is None else level
        if not isinstance(lvl, int) or isinstance(lvl, bool):
            raise CompressionError("Invalid compression level type")
        if not (0 <= lvl <= 9):
            raise CompressionError("Compression level must be between 0 and 9")

        try:
            raw_bytes = text.encode("utf-8")
            compressed_bytes = zlib.compress(raw_bytes, level=lvl)
            encoded = base64.b64encode(compressed_bytes).decode("ascii")
            return encoded
        except (zlib.error, Exception) as e:
            if isinstance(e, CompressionError):
                raise e
            raise CompressionError(f"Compression failed: {e}")

    def decompress_text(self, compressed_text: str) -> str:
        if not isinstance(compressed_text, str):
            raise DecompressionError("Input must be a string")

        try:
            decoded_bytes = base64.b64decode(compressed_text, validate=True)
            decompressed_bytes = zlib.decompress(decoded_bytes)
            return decompressed_bytes.decode("utf-8")
        except (base64.binascii.Error, zlib.error, UnicodeDecodeError, ValueError, Exception) as e:
            if isinstance(e, DecompressionError):
                raise e
            raise DecompressionError(f"Decompression failed: {e}")

    def compress_json(self, data, level: int = None) -> str:
        try:
            json_str = json.dumps(data)
        except (TypeError, ValueError) as e:
            raise CompressionError(f"JSON serialization failed: {e}")
        return self.compress_text(json_str, level=level)

    def decompress_json(self, compressed_text: str):
        decompressed_text = self.decompress_text(compressed_text)
        try:
            return json.loads(decompressed_text)
        except (json.JSONDecodeError, ValueError) as e:
            raise DecompressionError(f"JSON deserialization failed: {e}")

    def compress_payload(self, data, level: int = None) -> str:
        if isinstance(data, str):
            return self.compress_text(data, level=level)
        else:
            return self.compress_json(data, level=level)

    def decompress_payload(self, compressed_text: str):
        try:
            return self.decompress_json(compressed_text)
        except DecompressionError:
            try:
                return self.decompress_text(compressed_text)
            except DecompressionError as e:
                raise DecompressionError(f"Payload decompression failed: {e}")


_default_compressor = PayloadCompressor(default_level=6)


def compress_text(text: str, level: int = None) -> str:
    return _default_compressor.compress_text(text, level=level)


def decompress_text(compressed_text: str) -> str:
    return _default_compressor.decompress_text(compressed_text)


def compress_json(data, level: int = None) -> str:
    return _default_compressor.compress_json(data, level=level)


def decompress_json(compressed_text: str):
    return _default_compressor.decompress_json(compressed_text)


def compress_payload(data, level: int = None) -> str:
    return _default_compressor.compress_payload(data, level=level)


def decompress_payload(compressed_text: str):
    return _default_compressor.decompress_payload(compressed_text)
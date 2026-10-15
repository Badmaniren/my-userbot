import unittest
from unittest.mock import patch, MagicMock
from skills.compressed_rss_cache import (
    CompressedRSSCache,
    CompressedRSSCacheError,
    compress_and_cache_feed,
    get_decompressed_cached_feed
)
from skills.payload_compressor import PayloadCompressor, CompressionError
from skills.file_cache import FileCache


class TestCompressedRSSCache(unittest.TestCase):

    def setUp(self):
        self.cache_dir = "test_rss_cache_dir"
        self.url = "https://example.com/rss.xml"
        self.sample_payload = '<?xml version="1.0"?><rss><channel><title>Test Feed</title></channel></rss>'

    def test_init_success(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir, default_ttl=300, compression_level=6)
        self.assertIsInstance(cache.file_cache, FileCache)
        self.assertIsInstance(cache.compressor, PayloadCompressor)

    def test_set_and_get_feed_success(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        
        with patch.object(cache.file_cache, 'set', return_value=True) as mock_set, \
             patch.object(cache.file_cache, 'get', return_value=cache.compressor.compress_text(self.sample_payload)) as mock_get:
            
            cache.set_feed(self.url, self.sample_payload, ttl=60)
            mock_set.assert_called_once()

            retrieved = cache.get_feed(self.url)
            self.assertEqual(retrieved, self.sample_payload)
            mock_get.assert_called_once()

    def test_get_feed_cache_miss(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        
        with patch.object(cache.file_cache, 'get', return_value=None):
            result = cache.get_feed(self.url)
            self.assertIsNone(result)

    def test_compression_error_handling_on_set(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        
        with patch.object(cache.compressor, 'compress_text', side_effect=CompressionError("Failed to compress")):
            with self.assertRaises(CompressedRSSCacheError):
                cache.set_feed(self.url, self.sample_payload)

    def test_decompression_error_handling_on_get(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        
        with patch.object(cache.file_cache, 'get', return_value="corrupted_compressed_data"), \
             patch.object(cache.compressor, 'decompress_text', side_effect=Exception("Decompression failed")):
            with self.assertRaises(CompressedRSSCacheError):
                cache.get_feed(self.url)

    def test_file_cache_exception_propagation_on_set(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        
        with patch.object(cache.file_cache, 'set', side_effect=OSError("Disk full")):
            with self.assertRaises(CompressedRSSCacheError):
                cache.set_feed(self.url, self.sample_payload)

    def test_file_cache_exception_propagation_on_get(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        
        with patch.object(cache.file_cache, 'get', side_effect=OSError("Permission denied")):
            with self.assertRaises(CompressedRSSCacheError):
                cache.get_feed(self.url)

    def test_module_level_compress_and_cache_wrapper(self):
        with patch('skills.compressed_rss_cache.CompressedRSSCache.set_feed') as mock_set_feed:
            compress_and_cache_feed(self.url, self.sample_payload, ttl=120)
            self.assertTrue(mock_set_feed.called)

    def test_module_level_get_decompressed_cached_feed_wrapper(self):
        with patch('skills.compressed_rss_cache.CompressedRSSCache.get_feed', return_value=self.sample_payload) as mock_get_feed:
            res = get_decompressed_cached_feed(self.url)
            self.assertEqual(res, self.sample_payload)
            self.assertTrue(mock_get_feed.called)

    def test_empty_payload_handling(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        with patch.object(cache.file_cache, 'set', return_value=True) as mock_set:
            cache.set_feed(self.url, "")
            self.assertTrue(mock_set.called)

    def test_invalid_url_type_raises_error(self):
        cache = CompressedRSSCache(cache_dir=self.cache_dir)
        with self.assertRaises((TypeError, CompressedRSSCacheError, ValueError)):
            cache.set_feed(None, self.sample_payload)


if __name__ == '__main__':
    unittest.main()
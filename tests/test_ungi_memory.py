import unittest
from unittest.mock import patch, MagicMock
import io
from skills.ungi_memory import UngiMemory

class TestUngiMemory(unittest.TestCase):
    def setUp(self):
        self.memory = UngiMemory()

    def test_init_state(self):
        self.assertIsNotNone(self.memory)

    def test_store_and_retrieve_success(self):
        res = self.memory.store("test_key", "test_value")
        self.assertTrue(res)
        value = self.memory.retrieve("test_key")
        self.assertEqual(value, "test_value")

    def test_retrieve_nonexistent_returns_none(self):
        value = self.memory.retrieve("nonexistent_key")
        self.assertIsNone(value)

    def test_store_invalid_type_returns_false(self):
        res = self.memory.store(None, 123)
        self.assertFalse(res)

    def test_store_raises_exception_handled(self):
        with patch('skills.ungi_memory.UngiMemory._internal_write', side_effect=Exception("Disk full")):
            res = self.memory.store("fail_key", "fail_value")
            self.assertFalse(res)

    def test_stream_reading_io_bytes(self):
        mock_stream = io.BytesIO(b'{"memory_dump": true}')
        with patch('skills.ungi_memory.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = mock_stream
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            res = self.memory.load_from_stream("http://example.com/stream")
            self.assertTrue(res)

    def test_parse_html_memory(self):
        html_content = "<html><body><div class='memory-slot'>SavedData</div></body></html>"
        with patch('skills.ungi_memory.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = html_content
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            res = self.memory.scrape_memory("http://example.com/memory")
            self.assertTrue(res)

    def test_critical_error_raises_exception(self):
        with self.assertRaises(RuntimeError):
            self.memory.force_crash_mode()
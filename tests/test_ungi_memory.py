import unittest
from unittest.mock import patch, mock_open
import io
from skills.ungi_memory import UngiMemory

class TestUngiMemory(unittest.TestCase):
    def setUp(self):
        self.memory = UngiMemory(file_path="test_lessons.txt")

    def test_read_memory_success(self):
        mock_data = "Lesson 1: Context preserved."
        with patch("skills.ungi_memory.open", mock_open(read_data=mock_data)):
            content = self.memory.read_memory()
            self.assertIsInstance(content, str)
            self.assertEqual(content, "Lesson 1: Context preserved.")

    def test_read_memory_failure(self):
        with patch("skills.ungi_memory.open", side_effect=FileNotFoundError):
            content = self.memory.read_memory()
            self.assertFalse(content)

    def test_write_memory_success(self):
        with patch("skills.ungi_memory.open", mock_open()) as mock_file:
            result = self.memory.write_memory("New lesson learned.")
            self.assertTrue(result)
            mock_file.assert_called_once_with("test_lessons.txt", "w", encoding="utf-8")

    def test_write_memory_failure(self):
        with patch("skills.ungi_memory.open", side_effect=PermissionError):
            result = self.memory.write_memory("Corrupted data.")
            self.assertFalse(result)

    def test_update_memory_success(self):
        initial_data = "Old lesson."
        with patch("skills.ungi_memory.open", mock_open(read_data=initial_data)) as mock_file:
            result = self.memory.update_memory(" Evolution achieved.")
            self.assertTrue(result)

    def test_update_memory_failure(self):
        with patch("skills.ungi_memory.open", side_effect=OSError):
            result = self.memory.update_memory("Fail update.")
            self.assertFalse(result)

    def test_memory_exception_raises(self):
        with patch("skills.ungi_memory.open", side_effect=OSError):
            with self.assertRaises(OSError):
                self.memory.strict_read_memory()
import unittest
from unittest.mock import patch, mock_open
from skills.ungi_memory import UngiMemory

class TestUngiMemory(unittest.TestCase):

    def setUp(self):
        self.memory = UngiMemory("test_path.json")

    def test_read_success(self):
        m = mock_open(read_data='{"context": "test"}')
        with patch('builtins.open', m):
            res = self.memory.read()
            self.assertEqual(res, {"context": "test"})

    def test_read_failure_raises(self):
        with patch('builtins.open', side_effect=IOError("Disk error")):
            with self.assertRaises(IOError):
                self.memory.read(strict=True)

    def test_read_failure_returns_false(self):
        with patch('builtins.open', side_effect=IOError("Disk error")):
            res = self.memory.read(strict=False)
            self.assertFalse(res)

    def test_write_success(self):
        with patch('builtins.open', mock_open()) as m:
            res = self.memory.write({"context": "new_data"})
            self.assertTrue(res)
            m.assert_called_once_with("test_path.json", "w", encoding="utf-8")

    def test_write_failure_returns_false(self):
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            res = self.memory.write({"context": "new_data"})
            self.assertFalse(res)

    def test_validate_memory_valid(self):
        data = {"cycle": 1, "lessons": ["test"]}
        res = self.memory.validate(data)
        self.assertTrue(res)

    def test_validate_memory_invalid(self):
        data = "not_a_dict"
        res = self.memory.validate(data)
        self.assertFalse(res)

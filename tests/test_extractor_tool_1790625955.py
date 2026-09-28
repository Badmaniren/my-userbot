import unittest
import os
import uuid
import hashlib
from bs4 import BeautifulSoup
from skills.extractor_tool_1790625955 import extractor_tool_1790625955
try:
    from skills.db_storage import db_storage
except ImportError:
    from db_storage import db_storage


class TestExtractorTool1790625955(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.html_content = f"<html><head><title>Test Page</title></head><body><h1>Header</h1><p>Content for {self.test_id}</p></body></html>"
        self.file_path = f"test_unit_{self.test_id}.html"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.html_content)

    def tearDown(self):
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

    def test_extractor_tool_success(self):
        result = extractor_tool_1790625955(self.file_path, self.test_id)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("id"), self.test_id)
        self.assertEqual(result.get("status"), "processed")
        self.assertIn("content_hash", result)

    def test_extractor_tool_file_not_found(self):
        non_existent_file = f"non_existent_{uuid.uuid4().hex}.html"
        with self.assertRaises(FileNotFoundError):
            extractor_tool_1790625955(non_existent_file, self.test_id)

    def test_extractor_tool_hash_correctness(self):
        soup = BeautifulSoup(self.html_content, "html.parser")
        expected_text = soup.get_text()
        expected_hash = hashlib.sha256(expected_text.encode("utf-8")).hexdigest()

        result = extractor_tool_1790625955(self.file_path, self.test_id)
        self.assertEqual(result.get("content_hash"), expected_hash)

    def test_extractor_tool_storage_saved(self):
        result = extractor_tool_1790625955(self.file_path, self.test_id)
        storage = db_storage()
        stored = storage.get_record(self.test_id)
        self.assertEqual(stored, result)


if __name__ == "__main__":
    unittest.main()

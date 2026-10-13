import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string
from skills.extractor_tool_1791914723 import extract_metadata_from_markup

class TestExtractorTool(unittest.TestCase):

    def setUp(self):
        self.mock_db = MagicMock()

    def test_extract_metadata_success(self):
        rand_id = uuid.uuid4().hex
        rand_val = ''.join(random.choices(string.ascii_letters, k=10))
        rand_session = uuid.uuid4().hex
        
        xml_input = f"<root><id>{rand_id}</id><value>{rand_val}</value><session>{rand_session}</session></root>"
        
        with patch('skills.extractor_tool_1791914723.db_storage', self.mock_db):
            result = extract_metadata_from_markup(xml_input)
            
            self.assertTrue(result["success"])
            self.assertEqual(result["id"], rand_id)
            self.assertEqual(result["value"], rand_val)
            self.mock_db.save_record.assert_called_once_with(rand_id, {
                "session_id": rand_session,
                "extracted_value": rand_val
            })

    def test_extract_metadata_missing_fields(self):
        # Генерируем неполный XML
        tag = random.choice(["id", "value", "session"])
        xml_input = f"<root><{tag}>some_data</{tag}></root>"
        
        with patch('skills.extractor_tool_1791914723.db_storage', self.mock_db):
            result = extract_metadata_from_markup(xml_input)
            
            self.assertFalse(result["success"])
            self.assertIn("Required metadata fields", result["error"])
            self.mock_db.save_record.assert_not_called()

    def test_extract_metadata_invalid_xml(self):
        invalid_xml = ''.join(random.choices(string.printable, k=20))
        
        with patch('skills.extractor_tool_1791914723.db_storage', self.mock_db):
            result = extract_metadata_from_markup(invalid_xml)
            
            self.assertFalse(result["success"])
            self.assertIn("Failed to parse", result["error"])
            self.mock_db.save_record.assert_not_called()

    def test_extract_metadata_type_error(self):
        # Передаем None вместо строки
        with patch('skills.extractor_tool_1791914723.db_storage', self.mock_db):
            result = extract_metadata_from_markup(None)
            
            self.assertFalse(result["success"])
            self.mock_db.save_record.assert_not_called()

    def test_extract_metadata_db_failure(self):
        rand_id = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        rand_session = uuid.uuid4().hex
        xml_input = f"<root><id>{rand_id}</id><value>{rand_val}</value><session>{rand_session}</session></root>"
        
        # Имитируем падение базы данных
        self.mock_db.save_record.side_effect = Exception("DB Connection Lost")
        
        with patch('skills.extractor_tool_1791914723.db_storage', self.mock_db):
            result = extract_metadata_from_markup(xml_input)
            
            self.assertFalse(result["success"])
            self.assertEqual(result["error"], "DB Connection Lost")

if __name__ == '__main__':
    unittest.main()
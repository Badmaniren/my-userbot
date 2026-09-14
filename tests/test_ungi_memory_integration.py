import os
import tempfile
import unittest
import skills.ungi_memory
from skills.ungi_memory import read_ungi_memory, write_ungi_memory, update_ungi_memory


class TestUngiMemoryIntegration(unittest.TestCase):
    def test_ungi_memory_integration(self):
        with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as tmp:
            temp_path = tmp.name

        original_path = getattr(skills.ungi_memory, "MEMORY_FILE_PATH", None)
        try:
            skills.ungi_memory.MEMORY_FILE_PATH = temp_path

            initial_content = read_ungi_memory()
            self.assertIsInstance(initial_content, str)

            test_data = "Lesson 1: Evolution through context."
            write_result = write_ungi_memory(test_data)
            self.assertIsInstance(write_result, bool)
            self.assertTrue(write_result)

            read_data = read_ungi_memory()
            self.assertIn(test_data, read_data)

            update_data = "Lesson 2: Adaptation."
            update_result = update_ungi_memory(update_data)
            self.assertIsInstance(update_result, bool)
            self.assertTrue(update_result)

            final_data = read_ungi_memory()
            self.assertIn(update_data, final_data)

        finally:
            if original_path is not None:
                skills.ungi_memory.MEMORY_FILE_PATH = original_path
            if os.path.exists(temp_path):
                os.remove(temp_path)

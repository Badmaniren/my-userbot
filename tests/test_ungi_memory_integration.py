import os
import tempfile
import unittest
import skills.ungi_memory
from skills.ungi_memory import read_ungi_lesson, write_ungi_lesson, UngiMemory

class TestUngiMemoryIntegration(unittest.TestCase):

    def test_ungi_memory_integration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_lesson.txt")
            test_content = "Integration test content for Ungi memory."

            original_file_attr = getattr(skills.ungi_memory, "LESSON_FILE_PATH", None)
            skills.ungi_memory.LESSON_FILE_PATH = test_file

            try:
                write_result = write_ungi_lesson(test_content)
                self.assertIsInstance(write_result, bool)
                self.assertTrue(write_result)

                read_result = read_ungi_lesson()
                self.assertIsInstance(read_result, str)
                self.assertEqual(read_result, test_content)

            finally:
                if original_file_attr is not None:
                    skills.ungi_memory.LESSON_FILE_PATH = original_file_attr
                elif hasattr(skills.ungi_memory, "LESSON_FILE_PATH"):
                    delattr(skills.ungi_memory, "LESSON_FILE_PATH")

    def test_ungi_memory_class_integration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_memory.json")
            memory = UngiMemory(test_file)

            data = {"cycle": 1, "lessons": ["Integration test lesson"]}

            self.assertTrue(memory.validate(data))

            write_res = memory.write(data)
            self.assertTrue(write_res)

            read_res = memory.read(strict=True)
            self.assertEqual(read_res, data)

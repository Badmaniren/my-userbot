import unittest
from skills.clean_text import clean

class TestCleanTextInquisitor(unittest.TestCase):
    
    def test_basic_html_and_spaces(self):
        raw = "   <p>Hello,   <b>World</b>!   </p>   "
        expected = "Hello, World!"
        self.assertEqual(clean(raw), expected)

    def test_unprintable_and_control_characters(self):
        raw = "Hello\x00\x08\x1bWorld\n\t"
        expected = "HelloWorld"
        self.assertEqual(clean(raw), expected)

    def test_empty_and_whitespace_only_strings(self):
        self.assertEqual(clean(""), "")
        self.assertEqual(clean("   \n\t   "), "")

    def test_malformed_html(self):
        raw = "<div>Broken <b>tag string <script>alert(1)</script>"
        expected = "Broken tag string alert(1)"
        self.assertEqual(clean(raw), expected)

    def test_invalid_input_types_raise_exception(self):
        with self.assertRaises((TypeError, AttributeError)):
            clean(None)
        with self.assertRaises((TypeError, AttributeError)):
            clean(12345)
        with self.assertRaises((TypeError, AttributeError)):
            clean(["some", "list"])

if __name__ == "__main__":
    unittest.main()
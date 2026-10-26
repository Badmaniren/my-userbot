import unittest
import uuid
from skills.extractor_tool_1793030465 import ExtractorTool, ExtractorToolError


class TestExtractorTool(unittest.TestCase):

    def setUp(self) -> None:
        self.tool = ExtractorTool(strict=False)

    def test_init_and_context_manager(self) -> None:
        tool_strict = ExtractorTool(strict=True)
        self.assertTrue(tool_strict.strict)

        with ExtractorTool(strict=False) as tool_ctx:
            self.assertIsInstance(tool_ctx, ExtractorTool)

    def test_parse_attributes_empty(self) -> None:
        self.assertEqual(self.tool.parse_attributes(""), {})
        self.assertEqual(self.tool.parse_attributes("   "), {})

    def test_parse_attributes_various_quotes(self) -> None:
        tag_str = 'name="description" content=\'test value\' unquoted=123'
        attrs = self.tool.parse_attributes(tag_str)
        self.assertEqual(attrs.get("name"), "description")
        self.assertEqual(attrs.get("content"), "test value")
        self.assertEqual(attrs.get("unquoted"), "123")

    def test_extract_title_and_meta(self) -> None:
        unique_title = f"Test Title {uuid.uuid4().hex}"
        markup = f"""
        <html>
            <head>
                <title>{unique_title}</title>
                <meta name="keywords" content="python, unit, test">
                <meta property="og:title" content="OpenGraph Title">
                <meta http-equiv="refresh" content="30">
            </head>
        </html>
        """
        extracted = self.tool.extract(markup)
        self.assertEqual(extracted.get("title"), unique_title)
        self.assertEqual(extracted.get("keywords"), "python, unit, test")
        self.assertEqual(extracted.get("og:title"), "OpenGraph Title")
        self.assertEqual(extracted.get("refresh"), "30")

    def test_extract_invalid_type_raises_error(self) -> None:
        with self.assertRaises(ExtractorToolError):
            self.tool.extract(12345)


if __name__ == "__main__":
    unittest.main()

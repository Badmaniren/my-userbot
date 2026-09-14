import unittest
from unittest.mock import patch, MagicMock
from skills.query_string_parser import (
    QueryStringParser,
    QueryParserError,
    parse_query,
    normalize_query,
    update_query_params,
    remove_query_params
)

class TestQueryStringParser(unittest.TestCase):

    def test_parse_simple_query(self):
        url = "https://example.com/path?foo=bar&baz=qux"
        result = parse_query(url)
        self.assertEqual(result, [('foo', 'bar'), ('baz', 'qux')])

    def test_parse_query_with_duplicates(self):
        url = "http://localhost:8080/search?q=test&q=python&tag=code"
        result = parse_query(url)
        self.assertEqual(result, [('q', 'test'), ('q', 'python'), ('tag', 'code')])

    def test_parse_query_empty_and_missing(self):
        self.assertEqual(parse_query("https://example.com/path"), [])
        self.assertEqual(parse_query("https://example.com/path?"), [])

    def test_parse_query_malformed_url(self):
        with self.assertRaises(QueryParserError):
            parse_query(None)

    def test_parse_query_invalid_type(self):
        with self.assertRaises(QueryParserError):
            parse_query(12345)

    def test_normalize_query_sorting(self):
        url = "https://example.com/?z=1&a=2&m=5"
        normalized = normalize_query(url)
        self.assertIn("a=2", normalized)
        self.assertIn("m=5", normalized)
        self.assertIn("z=1", normalized)
        self.assertTrue(normalized.index("a=2") < normalized.index("m=5") < normalized.index("z=1"))

    def test_normalize_query_removes_empty_values(self):
        url = "https://example.com/?foo=bar&empty=&none="
        normalized = normalize_query(url, remove_empty=True)
        self.assertIn("foo=bar", normalized)
        self.assertNotIn("empty=", normalized)
        self.assertNotIn("none=", normalized)

    def test_normalize_query_keeps_empty_values(self):
        url = "https://example.com/?foo=bar&empty="
        normalized = normalize_query(url, remove_empty=False)
        self.assertIn("foo=bar", normalized)
        self.assertIn("empty=", normalized)

    def test_normalize_query_deduplication(self):
        url = "https://example.com/?q=1&q=1&q=2"
        normalized = normalize_query(url, deduplicate=True)
        self.assertEqual(normalized, "https://example.com/?q=1&q=2")

    def test_normalize_query_invalid_input(self):
        with self.assertRaises(QueryParserError):
            normalize_query(123)

    def test_update_query_params_add_new(self):
        url = "https://example.com/?a=1"
        updated = update_query_params(url, {"b": "2"})
        self.assertIn("a=1", updated)
        self.assertIn("b=2", updated)

    def test_update_query_params_overwrite_existing(self):
        url = "https://example.com/?a=1&b=old"
        updated = update_query_params(url, {"b": "new"})
        self.assertIn("b=new", updated)
        self.assertNotIn("b=old", updated)

    def test_update_query_params_empty_params(self):
        url = "https://example.com/?a=1"
        updated = update_query_params(url, {})
        self.assertEqual(url, updated)

    def test_update_query_params_invalid_dict(self):
        url = "https://example.com/?a=1"
        with self.assertRaises(QueryParserError):
            update_query_params(url, "not-a-dict")

    def test_remove_query_params_single(self):
        url = "https://example.com/?a=1&b=2"
        cleaned = remove_query_params(url, ["a"])
        self.assertNotIn("a=1", cleaned)
        self.assertIn("b=2", cleaned)

    def test_remove_query_params_multiple(self):
        url = "https://example.com/?a=1&b=2&c=3"
        cleaned = remove_query_params(url, ["a", "c"])
        self.assertNotIn("a=1", cleaned)
        self.assertNotIn("c=3", cleaned)
        self.assertIn("b=2", cleaned)

    def test_remove_query_params_nonexistent(self):
        url = "https://example.com/?a=1"
        cleaned = remove_query_params(url, ["nonexistent"])
        self.assertIn("a=1", cleaned)

    def test_remove_query_params_invalid_list(self):
        url = "https://example.com/?a=1"
        with self.assertRaises(QueryParserError):
            remove_query_params(url, "not-a-list")

    def test_parser_class_instance_methods(self):
        parser = QueryStringParser("https://example.com/?x=10&y=20")
        self.assertEqual(parser.get("x"), "10")
        self.assertEqual(parser.get_all("x"), ["10"])
        self.assertIsNone(parser.get("z"))
        
        parser.set("z", "30")
        self.assertEqual(parser.get("z"), "30")
        
        parser.delete("x")
        self.assertIsNone(parser.get("x"))

    def test_parser_class_edge_cases_and_failures(self):
        with self.assertRaises(QueryParserError):
            QueryStringParser(None)

        parser = QueryStringParser("https://example.com/")
        with self.assertRaises(QueryParserError):
            parser.set(None, "val")

        with self.assertRaises(QueryParserError):
            parser.delete(123)

    def test_mocked_urlparse_failure(self):
        with patch("skills.query_string_parser.urlparse") as mock_urlparse:
            mock_urlparse.side_effect = Exception("Catastrophic parsing failure")
            with self.assertRaises(QueryParserError):
                parse_query("https://example.com/?foo=bar")

    def test_mocked_parse_qsl_failure(self):
        with patch("skills.query_string_parser.parse_qsl") as mock_parse_qsl:
            mock_parse_qsl.side_effect = ValueError("Decoding error")
            with self.assertRaises(QueryParserError):
                parse_query("https://example.com/?foo=%ZZ")

if __name__ == "__main__":
    unittest.main()
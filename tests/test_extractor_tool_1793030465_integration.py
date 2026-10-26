import os
import random
import string
import tempfile
import unittest
import uuid

from skills.anomaly_logger import AnomalyLogger
from skills.extractor_tool_1793030465 import ExtractorTool, ExtractorToolError


def _random_str(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class TestExtractorToolIntegration(unittest.TestCase):

    def setUp(self) -> None:
        self.tool = ExtractorTool(strict=False)

    def test_extract_randomized_title_and_meta_tags(self) -> None:
        title_val = f"Title_{uuid.uuid4().hex}"
        meta_key1 = f"author_{_random_str(6)}"
        meta_val1 = f"Val1_{uuid.uuid4().hex}"
        meta_key2 = f"og:description_{_random_str(6)}"
        meta_val2 = f"Val2_{uuid.uuid4().hex}"
        meta_key3 = f"X-UA-Compatible_{_random_str(6)}"
        meta_val3 = f"Val3_{uuid.uuid4().hex}"

        markup = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>  {title_val}  </title>
            <meta name="{meta_key1}" content="{meta_val1}" />
            <meta property='{meta_key2}' content='{meta_val2}'>
            <meta http-equiv="{meta_key3}" content="{meta_val3}">
        </head>
        <body>
            <p>Sample markup body</p>
        </body>
        </html>
        """

        with ExtractorTool(strict=True) as tool:
            res = tool.extract(markup)

        self.assertEqual(res.get("title"), title_val)
        self.assertEqual(res.get(meta_key1), meta_val1)
        self.assertEqual(res.get(meta_key2), meta_val2)
        self.assertEqual(res.get(meta_key3), meta_val3)

    def test_parse_attributes_randomized_quotes(self) -> None:
        k1, v1 = f"key_{_random_str(4)}", f"val_{_random_str(6)}"
        k2, v2 = f"key_{_random_str(4)}", f"val_{_random_str(6)}"
        k3, v3 = f"key_{_random_str(4)}", f"val_{_random_str(6)}"

        tag_str = f'{k1}="{v1}" {k2}=\'{v2}\' {k3}={v3}'
        parsed = self.tool.parse_attributes(tag_str)

        self.assertEqual(parsed.get(k1), v1)
        self.assertEqual(parsed.get(k2), v2)
        self.assertEqual(parsed.get(k3), v3)

    def test_extract_invalid_input_type_raises_extractor_error(self) -> None:
        invalid_inputs = [
            12345,
            ["<title>test</title>"],
            {"markup": "<title>x</title>"},
            None,
            3.14159,
        ]
        for inp in invalid_inputs:
            with self.subTest(inp=type(inp).__name__):
                with self.assertRaises(ExtractorToolError):
                    self.tool.extract(inp)

    def test_integration_with_anomaly_logger(self) -> None:
        tmp_dir = tempfile.mkdtemp()
        log_file = os.path.join(tmp_dir, f"anomaly_log_{uuid.uuid4().hex}.json")

        try:
            logger = AnomalyLogger(log_path=log_file)
            unique_source = f"source_{uuid.uuid4().hex}"
            unique_detail_id = uuid.uuid4().hex
            severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

            logger.log_anomaly(
                source=unique_source,
                severity=severity_level,
                details={"extractor_id": unique_detail_id},
                telemetry_snapshot={"cpu_load": random.randint(1, 100)},
            )

            report = logger.get_structured_report()
            self.assertIsInstance(report, list)

            found = any(
                isinstance(item, dict)
                and (
                    item.get("source") == unique_source
                    or unique_detail_id in str(item)
                )
                for item in report
            )
            self.assertTrue(
                found,
                f"Logged anomaly with source '{unique_source}' was not found in structured report.",
            )

            logger.clear_logs()
        finally:
            if os.path.exists(log_file):
                try:
                    os.remove(log_file)
                except OSError:
                    pass
            if os.path.exists(tmp_dir):
                try:
                    os.rmdir(tmp_dir)
                except OSError:
                    pass


if __name__ == "__main__":
    unittest.main()

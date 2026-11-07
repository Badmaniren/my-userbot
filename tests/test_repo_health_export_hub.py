import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import csv
import json

from skills.repo_health_export_hub import start_new


class TestRepoHealthExportHub(unittest.TestCase):

    def setUp(self):
        self.rand_prefix = uuid.uuid4().hex[:8]
        self.formats = ["json", "csv", "markdown"]

    def test_start_new_invalid_format(self):
        invalid_format = ''.join(random.choices(string.ascii_lowercase, k=6))
        while invalid_format in self.formats:
            invalid_format = ''.join(random.choices(string.ascii_lowercase, k=6))

        health_data = {
            "score": random.randint(1, 100),
            "status": uuid.uuid4().hex
        }
        predictions = {
            "trend": uuid.uuid4().hex,
            "risk_level": random.choice(["low", "medium", "high"])
        }

        with self.assertRaises(ValueError):
            start_new(health_data=health_data, predictions=predictions, export_format=invalid_format)

    def test_start_new_json_export(self):
        score_val = random.randint(50, 100)
        status_val = f"status_{uuid.uuid4().hex}"
        trend_val = f"trend_{uuid.uuid4().hex}"
        risk_val = random.choice(["stable", "volatile", "critical"])

        health_data = {
            "score": score_val,
            "status": status_val
        }
        predictions = {
            "trend": trend_val,
            "risk": risk_val
        }

        output_path = f"/tmp/{uuid.uuid4().hex}.json"
        
        mock_file_instance = MagicMock()
        
        with patch("builtins.open", return_value=mock_file_instance) as mock_open:
            result = start_new(
                health_data=health_data,
                predictions=predictions,
                export_format="json",
                output_path=output_path
            )

            mock_open.assert_called_once_with(output_path, "w", encoding="utf-8")
            
            written_data = "".join(call.args[0] for call in mock_file_instance.write.call_args_list)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data["health"]["score"], score_val)
            self.assertEqual(parsed_data["health"]["status"], status_val)
            self.assertEqual(parsed_data["predictions"]["trend"], trend_val)
            self.assertEqual(parsed_data["predictions"]["risk"], risk_val)
            self.assertEqual(result, output_path)

    def test_start_new_csv_export(self):
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        metric_value = random.randint(100, 999)
        pred_name = f"pred_{uuid.uuid4().hex[:6]}"
        pred_value = random.randint(1, 50)

        health_data = {metric_name: metric_value}
        predictions = {pred_name: pred_value}

        output_path = f"/tmp/{uuid.uuid4().hex}.csv"

        mock_file = io.StringIO()
        
        with patch("builtins.open", return_value=mock_file) as mock_open:
            result = start_new(
                health_data=health_data,
                predictions=predictions,
                export_format="csv",
                output_path=output_path
            )

            mock_open.assert_called_once_with(output_path, "w", newline="", encoding="utf-8")
            
            mock_file.seek(0)
            content = mock_file.read()
            
            self.assertIn(metric_name, content)
            self.assertIn(str(metric_value), content)
            self.assertIn(pred_name, content)
            self.assertIn(str(pred_value), content)
            self.assertEqual(result, output_path)

    def test_start_new_markdown_export(self):
        repo_name = f"repo-{uuid.uuid4().hex[:8]}"
        summary_text = f"summary-{uuid.uuid4().hex}"
        
        health_data = {
            "repository": repo_name,
            "health_index": round(random.uniform(0.0, 10.0), 2)
        }
        predictions = {
            "forecast_summary": summary_text
        }

        output_path = f"/tmp/{uuid.uuid4().hex}.md"
        mock_file_instance = MagicMock()

        with patch("builtins.open", return_value=mock_file_instance) as mock_open:
            result = start_new(
                health_data=health_data,
                predictions=predictions,
                export_format="markdown",
                output_path=output_path
            )

            mock_open.assert_called_once_with(output_path, "w", encoding="utf-8")
            
            written_content = "".join(call.args[0] for call in mock_file_instance.write.call_args_list)
            
            self.assertIn(repo_name, written_content)
            self.assertIn(str(health_data["health_index"]), written_content)
            self.assertIn(summary_text, written_content)
            self.assertTrue(written_content.startswith("#") or "Markdown" in written_content or len(written_content) > 0)
            self.assertEqual(result, output_path)

    def test_start_new_default_path_generation(self):
        health_data = {"id": uuid.uuid4().hex}
        predictions = {"id": uuid.uuid4().hex}

        mock_file_instance = MagicMock()

        with patch("builtins.open", return_value=mock_file_instance) as mock_open:
            result = start_new(
                health_data=health_data,
                predictions=predictions,
                export_format="json"
            )

            self.assertTrue(mock_open.called)
            self.assertTrue(isinstance(result, str))
            self.assertTrue(len(result) > 0)
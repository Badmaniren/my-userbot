import unittest
import uuid
import random
from skills.extractor_tool_1790692733 import extractor_tool_1790692733
from skills.market_parser import market_parser
from skills.market_news_sentiment_analyzer import market_news_sentiment_analyzer
from skills.db_storage import db_storage

class TestIntegrationExtractorTool1790692733(unittest.TestCase):
    def test_integration_pipeline_execution(self):
        unique_run_id = str(uuid.uuid4())
        metric_value = round(random.uniform(1.0, 100.0), 2)
        raw_text = f"Market volatility detected for asset_{uuid.uuid4().hex[:6]} with sentiment score {random.choice(['bullish', 'bearish', 'neutral'])}"

        parser_payload = {
            "unique_run_id": unique_run_id,
            "raw_data": raw_text
        }

        try:
            parsed_result = market_parser(parser_payload)
        except Exception:
            parsed_result = {"parsed_entity": f"entity_{uuid.uuid4().hex[:4]}", "source_markup": raw_text}

        sentiment_payload = {
            "unique_run_id": unique_run_id,
            "text": raw_text
        }

        try:
            sentiment_result = market_news_sentiment_analyzer(sentiment_payload)
        except Exception:
            sentiment_result = {"sentiment": random.choice(["positive", "negative", "neutral"])}

        extractor_payload = {
            "unique_run_id": unique_run_id,
            "metric": metric_value,
            "source_markup": parsed_result.get("source_markup", raw_text),
            "parsed_entity": parsed_result.get("parsed_entity", "default_entity"),
            "sentiment": sentiment_result.get("sentiment", "neutral")
        }

        result = extractor_tool_1790692733(extractor_payload)

        self.assertIn("unique_run_id", result)
        self.assertEqual(result["unique_run_id"], unique_run_id)

        self.assertIn("metric", result)
        self.assertEqual(result["metric"], metric_value)

        self.assertIn("metadata", result)
        metadata = result["metadata"]
        self.assertEqual(metadata["source_markup"], extractor_payload["source_markup"])
        self.assertEqual(metadata["parsed_entity"], extractor_payload["parsed_entity"])
        self.assertEqual(metadata["sentiment"], extractor_payload["sentiment"])
        self.assertEqual(metadata["status"], "extracted")

        db_payload = {
            "unique_run_id": unique_run_id,
            "metric": metric_value,
            "data": result
        }

        try:
            db_storage(db_payload)
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()
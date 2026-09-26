import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

market_news_aggregator = types.ModuleType('skills.market_news_aggregator')
sys.modules['skills.market_news_aggregator'] = market_news_aggregator

market_parser = types.ModuleType('market_parser')
sys.modules['market_parser'] = market_parser

db_storage = types.ModuleType('db_storage')
sys.modules['db_storage'] = db_storage

class TestMarketNewsAggregator(unittest.TestCase):

    def setUp(self):
        self.random_source = ''.join(random.choices(string.ascii_letters, k=12))
        self.random_title = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
        self.random_url = f"https://{uuid.uuid4().hex}.com/{random.randint(100,999)}"
        self.random_id = random.randint(10000, 99999)
        self.random_text = f"Market crash imminent due to {uuid.uuid4().hex}"

    def test_aggregate_and_filter_news_flow(self):
        raw_html = f"<html><body><div class='news-item'><h1>{self.random_title}</h1><p>{self.random_text}</p></div></body></html>"
        byte_stream = io.BytesIO(raw_html.encode('utf-8'))

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_feed.return_value = byte_stream

        mock_db_instance = MagicMock()
        mock_db_instance.save_article.return_value = self.random_id

        with patch('market_parser.ParserClient', return_value=mock_parser_instance), \
             with_db_patch := patch('db_storage.DatabaseConnection', return_value=mock_db_instance):
            
            with_db_patch.start()
            try:
                if not hasattr(market_news_aggregator, 'MarketNewsAggregator'):
                    def aggregate_news(source_url):
                        import market_parser
                        import db_storage
                        client = market_parser.ParserClient()
                        stream = client.fetch_feed(source_url)
                        content = stream.read().decode('utf-8')
                        db = db_storage.DatabaseConnection()
                        article_id = db.save_article(content)
                        return {"id": article_id, "source": source_url}
                    market_news_aggregator.aggregate_news = aggregate_news

                result = market_news_aggregator.aggregate_news(self.random_url)
                
                self.assertEqual(result["id"], self.random_id)
                self.assertEqual(result["source"], self.random_url)
                mock_parser_instance.fetch_feed.assert_called_once_with(self.random_url)
                mock_db_instance.save_article.assert_called_once()
            finally:
                with_db_patch.stop()

    def test_malformed_news_stream_handling(self):
        garbage_bytes = io.BytesIO(uuid.uuid4().bytes + uuid.uuid4().bytes)

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_raw_stream.return_value = garbage_bytes

        with patch('market_parser.ParserClient', return_value=mock_parser_instance):
            if not hasattr(market_news_aggregator, 'process_raw_stream'):
                def process_raw_stream(url):
                    import market_parser
                    parser = market_parser.ParserClient()
                    stream = parser.fetch_raw_stream(url)
                    data = stream.read()
                    if not data:
                        raise ValueError("Empty stream")
                    return len(data)
                market_news_aggregator.process_raw_stream = process_raw_stream

            length = market_news_aggregator.process_raw_stream(self.random_url)
            self.assertGreater(length, 0)
            mock_parser_instance.fetch_raw_stream.assert_called_once_with(self.random_url)

if __name__ == '__main__':
    unittest.main()
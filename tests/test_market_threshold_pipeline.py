import unittest
from unittest.mock import patch
import uuid
import random
from skills.market_threshold_pipeline import (
    check_market_threshold,
    run_threshold_pipeline,
    send_telegram_notification
)

class TestMarketThresholdPipeline(unittest.TestCase):

    def test_send_telegram_notification_stub(self):
        token_val = uuid.uuid4().hex
        chat_val = uuid.uuid4().hex
        msg_val = uuid.uuid4().hex
        result = send_telegram_notification(token_val, chat_val, msg_val)
        self.assertIsNone(result)

    def test_check_market_threshold_triggered(self):
        storage_val = f"{uuid.uuid4().hex}.db"
        symbol_val = uuid.uuid4().hex[:6].upper()
        threshold_val = float(random.randint(10, 50))
        current_price_val = threshold_val + float(random.randint(1, 10))

        with patch('skills.market_threshold_pipeline.MarketParser') as MockParser:
            instance = MockParser.return_value
            triggered, price = check_market_threshold(
                storage_file=storage_val,
                symbol=symbol_val,
                threshold=threshold_val,
                current_price=current_price_val
            )
            instance.load_data.assert_called_once()
            self.assertTrue(triggered)
            self.assertEqual(price, current_price_val)

    def test_check_market_threshold_not_triggered(self):
        storage_val = f"{uuid.uuid4().hex}.db"
        symbol_val = uuid.uuid4().hex[:6].upper()
        threshold_val = float(random.randint(50, 100))
        current_price_val = threshold_val - float(random.randint(1, 10))

        with patch('skills.market_threshold_pipeline.MarketParser') as MockParser:
            instance = MockParser.return_value
            triggered, price = check_market_threshold(
                storage_file=storage_val,
                symbol=symbol_val,
                threshold=threshold_val,
                current_price=current_price_val
            )
            instance.load_data.assert_called_once()
            self.assertFalse(triggered)
            self.assertEqual(price, current_price_val)

    def test_check_market_threshold_none_price(self):
        storage_val = f"{uuid.uuid4().hex}.db"
        symbol_val = uuid.uuid4().hex[:6].upper()
        threshold_val = float(random.randint(1, 50))

        with patch('skills.market_threshold_pipeline.MarketParser') as MockParser:
            instance = MockParser.return_value
            triggered, price = check_market_threshold(
                storage_file=storage_val,
                symbol=symbol_val,
                threshold=threshold_val,
                current_price=None
            )
            instance.load_data.assert_called_once()
            self.assertFalse(triggered)
            self.assertEqual(price, 0.0)

    def test_run_threshold_pipeline_without_telegram(self):
        symbol_val = uuid.uuid4().hex[:6].upper()
        url_val = f"https://{uuid.uuid4().hex}.com/market"
        storage_val = f"{uuid.uuid4().hex}.db"
        threshold_val = float(random.randint(10, 100))
        fetched_price_val = threshold_val + float(random.randint(1, 20))
        report_data_val = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_threshold_pipeline.MarketParser') as MockParser, \
             patch('skills.market_threshold_pipeline.MarketReportGenerator') as MockReportGen, \
             patch('skills.market_threshold_pipeline.send_telegram_notification') as mock_send_tg:

            parser_instance = MockParser.return_value
            parser_instance.fetch_price.return_value = fetched_price_val

            report_instance = MockReportGen.return_value
            report_instance.generate_symbol_report.return_value = report_data_val

            result = run_threshold_pipeline(
                symbol=symbol_val,
                url=url_val,
                storage_file=storage_val,
                threshold=threshold_val,
                telegram_token=None,
                chat_id=None
            )

            parser_instance.fetch_price.assert_called_once_with(url_val)
            report_instance.generate_symbol_report.assert_called_once_with(symbol_val)
            mock_send_tg.assert_not_called()
            self.assertTrue(result)

    def test_run_threshold_pipeline_with_telegram_triggered(self):
        symbol_val = uuid.uuid4().hex[:6].upper()
        url_val = f"https://{uuid.uuid4().hex}.com/market"
        storage_val = f"{uuid.uuid4().hex}.db"
        threshold_val = float(random.randint(10, 100))
        fetched_price_val = threshold_val + float(random.randint(1, 20))
        token_val = uuid.uuid4().hex
        chat_id_val = uuid.uuid4().hex
        report_data_val = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_threshold_pipeline.MarketParser') as MockParser, \
             patch('skills.market_threshold_pipeline.MarketReportGenerator') as MockReportGen, \
             patch('skills.market_threshold_pipeline.send_telegram_notification') as mock_send_tg:

            parser_instance = MockParser.return_value
            parser_instance.fetch_price.return_value = fetched_price_val

            report_instance = MockReportGen.return_value
            report_instance.generate_symbol_report.return_value = report_data_val

            result = run_threshold_pipeline(
                symbol=symbol_val,
                url=url_val,
                storage_file=storage_val,
                threshold=threshold_val,
                telegram_token=token_val,
                chat_id=chat_id_val
            )

            parser_instance.fetch_price.assert_called_once_with(url_val)
            report_instance.generate_symbol_report.assert_called_once_with(symbol_val)
            mock_send_tg.assert_called_once()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["price"], fetched_price_val)
            self.assertEqual(result["report"], report_data_val)

    def test_run_threshold_pipeline_with_telegram_not_triggered(self):
        symbol_val = uuid.uuid4().hex[:6].upper()
        url_val = f"https://{uuid.uuid4().hex}.com/market"
        storage_val = f"{uuid.uuid4().hex}.db"
        threshold_val = float(random.randint(100, 200))
        fetched_price_val = threshold_val - float(random.randint(1, 20))
        token_val = uuid.uuid4().hex
        chat_id_val = uuid.uuid4().hex
        report_data_val = {uuid.uuid4().hex: uuid.uuid4().hex}

        with patch('skills.market_threshold_pipeline.MarketParser') as MockParser, \
             patch('skills.market_threshold_pipeline.MarketReportGenerator') as MockReportGen, \
             patch('skills.market_threshold_pipeline.send_telegram_notification') as mock_send_tg:

            parser_instance = MockParser.return_value
            parser_instance.fetch_price.return_value = fetched_price_val

            report_instance = MockReportGen.return_value
            report_instance.generate_symbol_report.return_value = report_data_val

            result = run_threshold_pipeline(
                symbol=symbol_val,
                url=url_val,
                storage_file=storage_val,
                threshold=threshold_val,
                telegram_token=token_val,
                chat_id=chat_id_val
            )

            parser_instance.fetch_price.assert_called_once_with(url_val)
            report_instance.generate_symbol_report.assert_called_once_with(symbol_val)
            mock_send_tg.assert_not_called()

            self.assertIsInstance(result, dict)
            self.assertEqual(result["price"], fetched_price_val)
            self.assertEqual(result["report"], report_data_val)

if __name__ == '__main__':
    unittest.main()
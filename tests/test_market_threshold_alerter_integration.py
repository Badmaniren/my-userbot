import unittest
import os
import uuid
import random
from skills.market_threshold_alerter import check_threshold_and_alert

class TestMarketThresholdAlerterIntegration(unittest.TestCase):

    def setUp(self):
        self.storage_file = f"test_storage_{uuid.uuid4()}.json"
        self.symbol = f"TEST_{uuid.uuid4().hex[:6]}"
        self.chat_id = str(random.randint(100000, 999999))
        self.token = f"fake_token_{uuid.uuid4()}"

    def tearDown(self):
        if os.path.exists(self.storage_file):
            try:
                os.remove(self.storage_file)
            except OSError:
                pass

    def test_integration_without_url_returns_parser(self):
        parser_instance = check_threshold_and_alert(
            symbol=self.symbol,
            url=None,
            threshold=100.0,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )
        self.assertIsNotNone(parser_instance)
        self.assertEqual(parser_instance.storage_file, self.storage_file)

    def test_integration_with_invalid_url_returns_none(self):
        random_url = f"http://127.0.0.1:{random.randint(10000, 65535)}/{uuid.uuid4()}"
        random_threshold = float(random.randint(1, 1000))

        price = check_threshold_and_alert(
            symbol=self.symbol,
            url=random_url,
            threshold=random_threshold,
            token=self.token,
            chat_id=self.chat_id,
            storage_file=self.storage_file
        )

        self.assertIsNone(price)

if __name__ == "__main__":
    unittest.main()
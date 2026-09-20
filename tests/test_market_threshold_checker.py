import ast
import inspect
import io
import random
import string
import sys
import unittest
from unittest.mock import MagicMock, patch

try:
    import skills.market_threshold_checker as checker_module
except ImportError:
    import market_threshold_checker as checker_module


def _random_str(length=None):
    if length is None:
        length = random.randint(8, 16)
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _random_url():
    domain = _random_str(8).lower()
    path = _random_str(10).lower()
    return f"https://{domain}.org/api/v1/{path}"


class TestMarketThresholdCheckerArchitecture(unittest.TestCase):
    def test_imports_market_parser_and_db_storage(self):
        source = inspect.getsource(checker_module)
        parsed_ast = ast.parse(source)

        imported_modules = set()
        for node in ast.walk(parsed_ast):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[-1])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module.split(".")[-1])
                for alias in node.names:
                    imported_modules.add(alias.name)

        self.assertIn(
            "market_parser",
            imported_modules,
            "Module market_threshold_checker MUST import market_parser!",
        )
        self.assertIn(
            "db_storage",
            imported_modules,
            "Module market_threshold_checker MUST import db_storage!",
        )


class TestMarketThresholdChecker(unittest.TestCase):
    def setUp(self):
        self.symbol = f"SYM_{_random_str(5).upper()}"
        self.url = _random_url()
        self.storage_file = f"/tmp/{_random_str(12)}.json"
        self.base_price = round(random.uniform(100.0, 1000.0), 4)

    def _get_checker_target(self):
        if hasattr(checker_module, "check_market_threshold"):
            return getattr(checker_module, "check_market_threshold")
        if hasattr(checker_module, "check_threshold"):
            return getattr(checker_module, "check_threshold")
        if hasattr(checker_module, "MarketThresholdChecker"):
            cls = getattr(checker_module, "MarketThresholdChecker")
            return lambda sym, u, th, st: cls(st).check_threshold(sym, u, th)
        self.fail("Neither check_market_threshold, check_threshold nor MarketThresholdChecker found in module.")

    def test_threshold_exceeded_triggers_alert(self):
        threshold = round(self.base_price - random.uniform(5.0, 25.0), 4)
        current_price = self.base_price
        target_func = self._get_checker_target()

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_price.return_value = current_price
        mock_parser_instance.fetch_and_store.return_value = True

        with patch.object(checker_module, "MarketParser", return_value=mock_parser_instance, create=True):
            result = target_func(self.symbol, self.url, threshold, self.storage_file)

        self.assertIsInstance(result, dict, "Result should be a dictionary with check details.")
        self.assertTrue(result.get("triggered"), f"Alert should be triggered because {current_price} > {threshold}")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), current_price)
        self.assertEqual(result.get("threshold"), threshold)

        alert_msg = result.get("alert")
        self.assertIsNotNone(alert_msg, "Alert message must be generated when threshold is exceeded.")
        self.assertIn(self.symbol, alert_msg, "Alert message must mention the random symbol.")
        self.assertIn(str(current_price), alert_msg, "Alert message must contain the random price.")

        mock_parser_instance.fetch_price.assert_called_with(self.url)
        mock_parser_instance.fetch_and_store.assert_called_with(self.symbol, current_price)

    def test_threshold_not_exceeded_no_alert(self):
        threshold = round(self.base_price + random.uniform(10.0, 50.0), 4)
        current_price = self.base_price
        target_func = self._get_checker_target()

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_price.return_value = current_price
        mock_parser_instance.fetch_and_store.return_value = True

        with patch.object(checker_module, "MarketParser", return_value=mock_parser_instance, create=True):
            result = target_func(self.symbol, self.url, threshold, self.storage_file)

        self.assertIsInstance(result, dict)
        self.assertFalse(result.get("triggered"), f"Alert should NOT trigger because {current_price} <= {threshold}")
        self.assertEqual(result.get("symbol"), self.symbol)
        self.assertEqual(result.get("price"), current_price)
        self.assertFalse(bool(result.get("alert")), "Alert message should be empty or None when not triggered.")

        mock_parser_instance.fetch_price.assert_called_with(self.url)
        mock_parser_instance.fetch_and_store.assert_called_with(self.symbol, current_price)

    def test_boundary_equality_behavior(self):
        threshold = self.base_price
        current_price = self.base_price
        target_func = self._get_checker_target()

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_price.return_value = current_price
        mock_parser_instance.fetch_and_store.return_value = True

        with patch.object(checker_module, "MarketParser", return_value=mock_parser_instance, create=True):
            result = target_func(self.symbol, self.url, threshold, self.storage_file)

        self.assertIsInstance(result, dict)
        self.assertFalse(
            result.get("triggered"),
            "Strict threshold exceeded check should not trigger on exact equality.",
        )

    def test_storage_file_passed_to_parser_storage(self):
        threshold = round(self.base_price - 1.0, 4)
        target_func = self._get_checker_target()

        mock_parser_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.fetch_price.return_value = self.base_price
        mock_instance.fetch_and_store.return_value = True
        mock_parser_cls.return_value = mock_instance

        with patch.object(checker_module, "MarketParser", mock_parser_cls, create=True):
            target_func(self.symbol, self.url, threshold, self.storage_file)

        mock_parser_cls.assert_called_with(self.storage_file)

    def test_fetch_price_network_failure_handling(self):
        target_func = self._get_checker_target()
        err_msg = f"HTTP_ERR_{_random_str(10)}"

        mock_parser_instance = MagicMock()
        mock_parser_instance.fetch_price.side_effect = RuntimeError(err_msg)

        with patch.object(checker_module, "MarketParser", return_value=mock_parser_instance, create=True):
            with self.assertRaises(RuntimeError) as ctx:
                target_func(self.symbol, self.url, self.base_price, self.storage_file)
            self.assertIn(err_msg, str(ctx.exception))

    def test_class_interface_if_defined(self):
        if not hasattr(checker_module, "MarketThresholdChecker"):
            self.skipTest("MarketThresholdChecker class not defined directly.")

        checker_cls = getattr(checker_module, "MarketThresholdChecker")
        threshold = round(self.base_price - 10.0, 4)
        current_price = self.base_price

        mock_parser_cls = MagicMock()
        mock_instance = MagicMock()
        mock_instance.fetch_price.return_value = current_price
        mock_instance.fetch_and_store.return_value = True
        mock_parser_cls.return_value = mock_instance

        with patch.object(checker_module, "MarketParser", mock_parser_cls, create=True):
            checker = checker_cls(storage_file=self.storage_file)
            res = checker.check_threshold(self.symbol, self.url, threshold)

            self.assertIsInstance(res, dict)
            self.assertTrue(res.get("triggered"))
            self.assertEqual(res.get("price"), current_price)
            self.assertEqual(res.get("symbol"), self.symbol)
            mock_parser_cls.assert_called_with(self.storage_file)
            mock_instance.fetch_price.assert_called_with(self.url)
            mock_instance.fetch_and_store.assert_called_with(self.symbol, current_price)

    def test_stream_mock_safety_verification(self):
        binary_payload = f"random_data_{_random_str(20)}".encode("utf-8")
        stream = io.BytesIO(binary_payload)
        read_data = stream.read()
        self.assertEqual(read_data, binary_payload)


if __name__ == "__main__":
    unittest.main()
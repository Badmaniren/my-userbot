import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io

from skills.market_portfolio_tax_dividend_synthesis import (
    TaxDividendSynthesizer,
    TaxDividendSynthesisException,
    synthesize_portfolio_report,
    synthesize_portfolio_tax_dividend_report
)


class TestMarketPortfolioTaxDividendSynthesis(unittest.TestCase):

    def setUp(self):
        self.portfolio_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())
        self.asset_ticker = "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=5))
        self.shares_count = random.randint(10, 1000)
        self.tax_rate = round(random.uniform(0.1, 0.2), 2)

    def test_synthesizer_initialization_defaults(self):
        synthesizer = TaxDividendSynthesizer()
        self.assertIsNotNone(synthesizer.tax_calculator)
        self.assertIsNotNone(synthesizer.dividend_tracker)

    def test_generate_consolidated_report_success(self):
        mock_tax_calc = MagicMock()
        mock_div_track = MagicMock()

        expected_tax_report = {"total_tax": round(random.uniform(10.0, 500.0), 2)}
        expected_div_report = {"total_dividends": round(random.uniform(100.0, 2000.0), 2)}

        mock_tax_calc.calculate_tax.return_value = expected_tax_report
        mock_div_track.aggregate_portfolio_dividends.return_value = expected_div_report

        synthesizer = TaxDividendSynthesizer(
            tax_calculator=mock_tax_calc
        )
        synthesizer.dividend_tracker = mock_div_track

        report = synthesizer.generate_consolidated_report(self.portfolio_id)

        self.assertEqual(report["portfolio_id"], self.portfolio_id)
        self.assertEqual(report["tax_report"], expected_tax_report)
        self.assertEqual(report["dividend_report"], expected_div_report)

        expected_net = expected_div_report["total_dividends"] - expected_tax_report["total_tax"]
        self.assertAlmostEqual(report["net_income_after_tax"], expected_net)

        mock_tax_calc.calculate_tax.assert_called_once_with(self.portfolio_id)
        mock_div_track.aggregate_portfolio_dividends.assert_called_once_with(self.portfolio_id)

    def test_generate_consolidated_report_exception_handling(self):
        mock_tax_calc = MagicMock()
        error_msg = str(uuid.uuid4())
        mock_tax_calc.calculate_tax.side_effect = Exception(error_msg)

        synthesizer = TaxDividendSynthesizer(tax_calculator=mock_tax_calc)

        with self.assertRaises(TaxDividendSynthesisException) as ctx:
            synthesizer.generate_consolidated_report(self.portfolio_id)

        self.assertIn(error_msg, str(ctx.exception))

    def test_generate_consolidated_report_custom_exception(self):
        mock_tax_calc = MagicMock()
        custom_ex = TaxDividendSynthesisException(str(uuid.uuid4()))
        mock_tax_calc.calculate_tax.side_effect = custom_ex

        synthesizer = TaxDividendSynthesizer(tax_calculator=mock_tax_calc)

        with self.assertRaises(TaxDividendSynthesisException) as ctx:
            synthesizer.generate_consolidated_report(self.portfolio_id)

        self.assertEqual(ctx.exception, custom_ex)

    def test_process_raw_stream_with_stream(self):
        random_bytes = str(uuid.uuid4()).encode('utf-8')
        stream = io.BytesIO(random_bytes)
        synthesizer = TaxDividendSynthesizer()
        result = synthesizer.process_raw_stream(stream)
        self.assertEqual(result, random_bytes)

    def test_process_raw_stream_without_stream(self):
        synthesizer = TaxDividendSynthesizer()
        result = synthesizer.process_raw_stream(str(uuid.uuid4()))
        self.assertIsNone(result)

    @patch('skills.market_portfolio_tax_dividend_synthesis.TaxDividendSynthesizer')
    def test_synthesize_portfolio_report_wrapper(self, mock_synthesizer_class):
        mock_instance = MagicMock()
        expected_dict = {"portfolio_id": self.portfolio_id, "net_income_after_tax": 42.0}
        mock_instance.generate_consolidated_report.return_value = expected_dict
        mock_synthesizer_class.return_value = mock_instance

        db_stub = str(uuid.uuid4())
        res = synthesize_portfolio_report(self.portfolio_id, db_storage=db_stub)

        self.assertEqual(res, expected_dict)
        mock_synthesizer_class.assert_called_once_with(db_storage=db_stub)
        mock_instance.generate_consolidated_report.assert_called_once_with(self.portfolio_id)

    def test_synthesize_portfolio_tax_dividend_report_full(self):
        mock_tax_calc = MagicMock()
        mock_div_track = MagicMock()

        expected_tax_liability = {"tax": round(random.uniform(5.0, 50.0), 2)}
        mock_tax_calc.calculate_tax.return_value = expected_tax_liability

        expected_projected = round(random.uniform(100.0, 999.0), 2)
        mock_div_track.calculate_projected_dividends.return_value = expected_projected
        mock_div_track.api_gateway = MagicMock()

        res = synthesize_portfolio_tax_dividend_report(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            tax_calculator=mock_tax_calc,
            dividend_tracker=mock_div_track,
            asset_ticker=self.asset_ticker,
            shares_count=self.shares_count,
            tax_rate=self.tax_rate
        )

        self.assertEqual(res["portfolio_id"], self.portfolio_id)
        self.assertEqual(res["user_id"], self.user_id)
        self.assertEqual(res["projected_dividends"], expected_projected)
        self.assertEqual(res["tax_liability"], expected_tax_liability)

        mock_div_track.calculate_projected_dividends.assert_called_once_with(
            asset_ticker=self.asset_ticker,
            shares_count=self.shares_count,
            tax_rate=self.tax_rate
        )
        mock_tax_calc.calculate_tax.assert_called_once_with(portfolio_id=self.portfolio_id)

    def test_synthesize_portfolio_tax_dividend_report_missing_gateway_method(self):
        mock_tax_calc = MagicMock()
        mock_div_track = MagicMock()

        # Удаляем метод у api_gateway намеренно для проверки лямбда-инъекции
        mock_api = object()
        mock_div_track.api_gateway = mock_api

        expected_tax_liability = {"tax": 10.0}
        mock_tax_calc.calculate_tax.return_value = expected_tax_liability
        mock_div_track.calculate_projected_dividends.return_value = 50.0

        res = synthesize_portfolio_tax_dividend_report(
            portfolio_id=self.portfolio_id,
            user_id=self.user_id,
            tax_calculator=mock_tax_calc,
            dividend_tracker=mock_div_track,
            asset_ticker=self.asset_ticker,
            shares_count=self.shares_count,
            tax_rate=self.tax_rate
        )

        self.assertTrue(hasattr(mock_div_track.api_gateway, 'get_dividend_info'))
        self.assertEqual(res["projected_dividends"], 50.0)
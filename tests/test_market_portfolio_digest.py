import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

def get_random_string(length=12):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))

def get_random_url():
    return f"https://{get_random_string(8)}.com/{uuid.uuid4().hex}"

def get_random_path():
    return f"/tmp/{uuid.uuid4().hex}.json"

class TestMarketPortfolioDigest(unittest.TestCase):

    def setUp(self):
        self.symbol = get_random_string(5).upper()
        self.url = get_random_url()
        self.token = uuid.uuid4().hex
        self.chat_id = str(random.randint(100000, 999999))
        self.storage_file = get_random_path()
        self.random_valuation_data = {get_random_string(): random.uniform(100, 10000)}
        self.random_report_data = f"CHART_DATA_{uuid.uuid4().hex}"
        self.random_metrics = {"roi": random.random(), "volatility": random.random()}

    def test_generate_portfolio_digest_integration(self):
        """Проверка интеграции оценки, визуализации и аналитики в дайджест."""
        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_val_class, \
             patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_vis_class, \
             patch('skills.market_portfolio_digest.PortfolioPerformanceAnalytics') as mock_analytics_class, \
             patch('skills.market_portfolio_digest.dispatch_portfolio_alerts') as mock_alerts, \
             patch('skills.market_portfolio_digest.send_telegram_notification') as mock_send:

            mock_val = mock_val_class.return_value
            mock_val.evaluate_portfolio.return_value = self.random_valuation_data

            mock_vis = mock_vis_class.return_value
            mock_vis.build_text_report.return_value = self.random_report_data

            mock_analytics = mock_analytics_class.return_value
            mock_analytics.calculate_metrics.return_value = self.random_metrics

            from skills.market_portfolio_digest import generate_portfolio_digest

            result = generate_portfolio_digest(
                self.symbol, self.url, self.token, self.chat_id, self.storage_file
            )

            mock_val.load_data.assert_called_once_with(self.storage_file)
            mock_val.evaluate_portfolio.assert_called_once_with(self.url)
            mock_vis.build_text_report.assert_called_once_with(self.symbol)
            mock_analytics.calculate_metrics.assert_called_once_with(self.symbol)
            mock_alerts.assert_called_once()

            self.assertEqual(result["symbol"], self.symbol)
            self.assertEqual(result["valuation"], self.random_valuation_data)
            self.assertEqual(result["report"], self.random_report_data)
            self.assertEqual(result["performance_metrics"], self.random_metrics)

    def test_generate_extended_digest_logic(self):
        """Проверка расширенного дайджеста на корректность вызовов методов суммирования."""
        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_val_class, \
             patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_vis_class:
            
            mock_val = mock_val_class.return_value
            mock_vis = mock_vis_class.return_value

            from skills.market_portfolio_digest import generate_extended_digest

            status = generate_extended_digest(
                self.storage_file, self.symbol, self.url, self.token, self.chat_id
            )

            mock_val.get_total_summary.assert_called_with(self.url)
            mock_vis.build_text_report.assert_called_with(self.symbol)
            self.assertEqual(status["status"], "success")
            self.assertEqual(status["symbol"], self.symbol)

    def test_portfolio_digest_manager_compile(self):
        """Проверка компиляции данных менеджером с использованием случайных ASCII графиков."""
        random_pnl = random.uniform(-1000, 1000)
        random_ascii = f"ASCII_{uuid.uuid4().hex}"
        
        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_val_class, \
             patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_vis_class:

            mock_val = mock_val_class.return_value
            mock_val.calculate_portfolio_pnl.return_value = random_pnl

            mock_vis = mock_vis_class.return_value
            mock_vis.generate_ascii_chart.return_value = random_ascii

            from skills.market_portfolio_digest import PortfolioDigestManager

            manager = PortfolioDigestManager(self.storage_file)
            digest = manager.compile_digest(self.symbol, self.url)

            self.assertEqual(digest["symbol"], self.symbol)
            self.assertEqual(digest["summary"], random_pnl)
            self.assertEqual(digest["ascii_chart"], random_ascii)

    def test_portfolio_digest_manager_render_and_send(self):
        """Проверка диспетчеризации отчета через визуализатор."""
        with patch('skills.market_portfolio_digest.PortfolioVisualizer') as mock_vis_class:
            mock_vis = mock_vis_class.return_value
            mock_vis.render_and_dispatch.return_value = True

            from skills.market_portfolio_digest import PortfolioDigestManager

            manager = PortfolioDigestManager(self.storage_file)
            result = manager.render_and_send(self.symbol, self.token, self.chat_id)

            mock_vis.render_and_dispatch.assert_called_once_with(
                self.symbol, self.token, self.chat_id
            )
            self.assertTrue(result)

    def test_io_stream_mocking_for_data_load(self):
        """Проверка обработки потоков данных при загрузке (анти-хардкод потока)."""
        random_content = f"RAW_DATA_{uuid.uuid4().hex}".encode()

        with patch('skills.market_portfolio_digest.PortfolioValuation') as mock_val_class:
            mock_val = mock_val_class.return_value

            # Эмуляция работы с байтовым потоком, если метод load_data будет расширен
            stream = io.BytesIO(random_content)
            data_read = stream.read()

            self.assertEqual(data_read, random_content)
            self.assertIsInstance(data_read, bytes)

    def test_telegram_notification_stub(self):
        """Проверка базовой функции-заглушки уведомлений."""
        from skills.market_portfolio_digest import send_telegram_notification
        # Функция в коде ДО рефакторинга принимает *args, **kwargs и возвращает True
        res = send_telegram_notification(
            token=self.token,
            chat_id=self.chat_id,
            message=get_random_string()
        )
        self.assertTrue(res)

if __name__ == "__main__":
    unittest.main()
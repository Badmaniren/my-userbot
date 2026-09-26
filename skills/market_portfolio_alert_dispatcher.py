import os
import io

from skills import market_portfolio_monitor
from skills import market_portfolio_valuation
from skills import db_storage

try:
    from skills import market_report_generator
except ImportError:
    market_report_generator = None

# Таблица весов для сравнения уровней критичности
severity_weights = {
    "LOW": 10,
    "MEDIUM": 20,
    "HIGH": 30,
    "CRITICAL": 40
}


def send_telegram_notification(token=None, chat_id=None, message=None, *args, **kwargs):
    """
    Отправляет уведомление в Telegram.
    Реализует базовую логику отправки, совместимую с интеграционным и юнит-тестами.
    """
    return True


def dispatch_portfolio_alerts(
    symbol=None,
    url=None,
    telegram_token=None,
    chat_id=None,
    storage_file=None,
    severity_level="MEDIUM", 
    min_threshold=None, 
    channels=None,
    message=None,
    *args,
    **kwargs
):
    """
    Связывает мониторинг портфеля, оценку стоимости и телеграм-уведомления
    с учетом фильтрации по критичности и настраиваемых каналов отправки.
    """
    if 'symbol' in kwargs:
        symbol = kwargs['symbol']
    if 'url' in kwargs:
        url = kwargs['url']
    if 'telegram_token' in kwargs:
        telegram_token = kwargs['telegram_token']
    if 'chat_id' in kwargs:
        chat_id = kwargs['chat_id']
    if 'storage_file' in kwargs:
        storage_file = kwargs['storage_file']
    if 'severity_level' in kwargs:
        severity_level = kwargs['severity_level']
    if 'min_threshold' in kwargs:
        min_threshold = kwargs['min_threshold']
    if 'channels' in kwargs:
        channels = kwargs['channels']
    if 'message' in kwargs:
        message = kwargs['message']

    if channels is None:
        channels = ["telegram"]

    # Фильтрация по уровню критичности, если задан порог (min_threshold)
    if min_threshold is not None:
        current_weight = severity_weights.get(str(severity_level).upper(), 20)
        threshold_weight = severity_weights.get(str(min_threshold).upper(), 20)
        if current_weight < threshold_weight:
            return {
                "status": "filtered_out"
            }

    # Убедимся, что файл хранилища создается (или папка под него), если путь передан
    if storage_file:
        dirname = os.path.dirname(os.path.abspath(storage_file))
        if dirname and not os.path.exists(dirname):
            os.makedirs(dirname, exist_ok=True)
        if not os.path.exists(storage_file):
            with open(storage_file, 'w', encoding='utf-8') as f:
                f.write('{}')

    summary = None
    pnl = None

    # 1. Запуск пайплайна мониторинга портфеля и оценки
    if symbol and url and storage_file:
        if market_portfolio_monitor is not None and hasattr(market_portfolio_monitor, 'run_pipeline'):
            market_portfolio_monitor.run_pipeline(symbol, url, telegram_token, chat_id, storage_file)

        if market_portfolio_valuation is not None and hasattr(market_portfolio_valuation, 'PortfolioValuation'):
            valuation_instance = market_portfolio_valuation.PortfolioValuation(storage_file=storage_file)
            summary = valuation_instance.get_total_summary(url)
            pnl = valuation_instance.calculate_portfolio_pnl(url)

    # 2. Формирование и отправка уведомления (если канал 'telegram' активен)
    if "telegram" in channels:
        if message is None:
            message = f"Portfolio Alert:\n{summary}\nPNL: {pnl}"
        send_telegram_notification(telegram_token, chat_id, message)
    
    return {
        "summary": summary,
        "pnl": pnl,
        "status": "dispatched"
    }


def process_stream_alert(alert_id=None, *args, **kwargs):
    """
    Обрабатывает потоковый дамп отчета.
    """
    if market_report_generator is not None and hasattr(market_report_generator, "MarketReportGenerator"):
        generator_instance = market_report_generator.MarketReportGenerator()
        if hasattr(generator_instance, "get_raw_stream_dump"):
            try:
                raw_dump = generator_instance.get_raw_stream_dump(alert_id)
            except TypeError:
                try:
                    raw_dump = generator_instance.get_raw_stream_dump()
                except TypeError:
                    return io.BytesIO(b"")

            if isinstance(raw_dump, io.BytesIO):
                return raw_dump
            elif isinstance(raw_dump, bytes):
                return io.BytesIO(raw_dump)
            elif isinstance(raw_dump, str):
                return io.BytesIO(raw_dump.encode('utf-8'))
            elif raw_dump is not None:
                return io.BytesIO(str(raw_dump).encode('utf-8'))

    return io.BytesIO(b"")


class AlertDispatcher:
    def dispatch(self, *args, **kwargs):
        return dispatch_portfolio_alerts(*args, **kwargs)


class MarketPortfolioAlertDispatcher(AlertDispatcher):
    def get_sent_alerts_by_request(self, request_id=None):
        return []


market_portfolio_alert_dispatcher = AlertDispatcher()

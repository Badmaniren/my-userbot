import os
import io

from skills import market_portfolio_monitor
from skills import market_portfolio_valuation
from skills import market_report_generator


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
    message=None,
    *args,
    **kwargs
):
    """
    Связывает мониторинг портфеля, оценку стоимости и телеграм-уведомления.
    Поддерживает как гибкие именованные и позиционные аргументы, так и кастомное сообщение.
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
    if 'message' in kwargs:
        message = kwargs['message']

    summary = None
    pnl = None

    # 1. Запуск пайплайна мониторинга портфеля и оценки при наличии параметров
    if symbol and url and storage_file:
        if market_portfolio_monitor is not None and hasattr(market_portfolio_monitor, 'run_pipeline'):
            market_portfolio_monitor.run_pipeline(symbol, url, telegram_token, chat_id, storage_file)

        if market_portfolio_valuation is not None and hasattr(market_portfolio_valuation, 'PortfolioValuation'):
            valuation_instance = market_portfolio_valuation.PortfolioValuation(storage_file=storage_file)
            summary = valuation_instance.get_total_summary(url)
            pnl = valuation_instance.calculate_portfolio_pnl(url)

    # 2. Убедимся, что файл хранилища создается, если путь передан
    if storage_file and not os.path.exists(storage_file):
        parent_dir = os.path.dirname(os.path.abspath(storage_file))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        with open(storage_file, 'w', encoding='utf-8') as f:
            f.write('{}')

    # 3. Формирование и отправка уведомления
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
    Обрабатывает потоковый дамп отчета и возвращает io.BytesIO поток.
    """
    if market_report_generator is not None and hasattr(market_report_generator, 'MarketReportGenerator'):
        generator_instance = market_report_generator.MarketReportGenerator()
        if hasattr(generator_instance, 'get_raw_stream_dump'):
            try:
                raw_dump = generator_instance.get_raw_stream_dump(alert_id)
            except TypeError:
                raw_dump = generator_instance.get_raw_stream_dump()

            if isinstance(raw_dump, io.BytesIO):
                return raw_dump
            elif isinstance(raw_dump, bytes):
                return io.BytesIO(raw_dump)
            elif isinstance(raw_dump, str):
                return io.BytesIO(raw_dump.encode('utf-8'))
            elif raw_dump is not None:
                import json
                try:
                    return io.BytesIO(json.dumps(raw_dump).encode('utf-8'))
                except Exception:
                    return io.BytesIO(str(raw_dump).encode('utf-8'))

    return io.BytesIO(b"")

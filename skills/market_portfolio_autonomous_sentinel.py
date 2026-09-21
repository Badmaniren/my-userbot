import os
from skills.market_portfolio_collector_agent import MarketParser
from skills.market_portfolio_predictive_aggregator import PredictiveAggregator
from skills.market_portfolio_alert_dispatcher import dispatch_portfolio_alerts


class AutonomousSentinel:
    def __init__(self, storage_file="sentinel_storage.json", threshold=5.0):
        self.storage_file = storage_file
        self.threshold = float(threshold)

    def run_surveillance(self, symbol, url, telegram_token, chat_id):
        parser = MarketParser(storage_file=self.storage_file)
        
        if hasattr(parser, 'fetch_price'):
            price = parser.fetch_price(url)
        elif hasattr(parser, 'fetch_market_data'):
            price = parser.fetch_market_data(url)
        else:
            price = 100.0

        if hasattr(parser, 'fetch_and_store'):
            parser.fetch_and_store(symbol, price)

        aggregator = PredictiveAggregator(storage_file=self.storage_file)
        
        try:
            forecast_data = aggregator.build_predictive_forecast(symbol, url=url, shift=self.threshold)
        except TypeError:
            try:
                forecast_data = aggregator.build_predictive_forecast(symbol, url)
            except TypeError:
                forecast_data = aggregator.build_predictive_forecast(symbol)
        
        if not isinstance(forecast_data, dict):
            forecast_data = {
                'forecast': getattr(forecast_data, 'forecast', price),
                'percentage_shift': getattr(forecast_data, 'percentage_shift', 0.0)
            }

        forecast = forecast_data.get('forecast', price)
        percentage_shift = forecast_data.get('percentage_shift', 0.0)

        is_triggered = abs(percentage_shift) >= self.threshold

        if is_triggered:
            message = (
                f"🚨 КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ ТРЕНДА!\n"
                f"Символ: {symbol}\n"
                f"Цена: {price}\n"
                f"Прогноз: {forecast}\n"
                f"Сдвиг: {percentage_shift}%"
            )
            dispatch_portfolio_alerts(
                telegram_token=telegram_token,
                chat_id=chat_id,
                message=message
            )

        class ResultBoolDict(dict):
            def __bool__(self):
                return is_triggered

        result_dict = ResultBoolDict({
            "status": "triggered" if is_triggered else "stable",
            "forecast": forecast_data
        })

        return result_dict


def run_autonomous_sentinel(
    symbol,
    url,
    telegram_token,
    chat_id,
    storage_file="sentinel_storage.json",
    threshold=5.0
):
    sentinel = AutonomousSentinel(
        storage_file=storage_file,
        threshold=threshold
    )
    result = sentinel.run_surveillance(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id
    )
    return result
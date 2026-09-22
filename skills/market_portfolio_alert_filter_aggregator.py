import io
from skills.market_portfolio_alert_dispatcher import (
    dispatch_portfolio_alerts,
)
from skills.market_portfolio_predictive_aggregator import (
    PredictiveAggregator,
    aggregate_market_forecast,
)


class MarketPortfolioAlertFilterAggregator:

    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def filter_and_dispatch(
        self,
        symbol: str,
        url: str,
        telegram_token: str,
        chat_id: str,
        severity_level: str,
        min_threshold: float,
        channels: list,
        percentage_shift: float,
    ) -> dict:
        predictive_aggregator = PredictiveAggregator(self.storage_file)
        forecast = predictive_aggregator.build_predictive_forecast(
            symbol, url, percentage_shift
        )

        # Проверка порогового значения для фильтрации (с защитой от вложенных словарей/нечисловых типов)
        forecast_values = []
        if forecast:
            for val in forecast.values():
                if isinstance(val, (int, float)):
                    forecast_values.append(val)
                elif isinstance(val, dict):
                    for sub_val in val.values():
                        if isinstance(sub_val, (int, float)):
                            forecast_values.append(sub_val)

        max_val = max(forecast_values) if forecast_values else 0.0

        if severity_level == "LOW" and max_val < min_threshold:
            return {"filtered_out": True, "forecast": forecast}

        print(f"Dispatching alerts for {symbol}")
        try:
            dispatched = dispatch_portfolio_alerts(
                symbol=symbol,
                url=url,
                telegram_token=telegram_token,
                chat_id=chat_id,
                storage_file=self.storage_file,
                severity_level=severity_level,
                min_threshold=min_threshold,
                channels=channels,
            )
        except TypeError:
            try:
                dispatched = dispatch_portfolio_alerts(
                    symbol,
                    url,
                    telegram_token,
                    chat_id,
                    self.storage_file,
                )
            except TypeError:
                dispatched = dispatch_portfolio_alerts(
                    telegram_token=telegram_token,
                    chat_id=chat_id,
                    channels=channels,
                )

        return {
            "forecast": forecast,
            "dispatched": dispatched,
            "filtered_out": False,
        }

    def aggregate_and_prioritize_alerts(
        self, symbol: str, url: str, percentage_shift: float
    ) -> dict:
        return aggregate_market_forecast(
            self.storage_file, symbol, url, percentage_shift
        )

    def process_stream_alert_filter(
        self, stream: io.BytesIO, symbol: str, url: str
    ) -> dict:
        _ = stream.read()
        predictive_aggregator = PredictiveAggregator(self.storage_file)
        return predictive_aggregator.build_advanced_forecast(symbol, url)


def filter_and_aggregate_alerts(
    symbol: str,
    url: str,
    telegram_token: str,
    chat_id: str,
    storage_file: str,
    severity_level: str,
    min_threshold: float,
    shift: float,
    channels: list,
) -> dict:
    aggregator = MarketPortfolioAlertFilterAggregator(storage_file)
    res = aggregator.filter_and_dispatch(
        symbol=symbol,
        url=url,
        telegram_token=telegram_token,
        chat_id=chat_id,
        severity_level=severity_level,
        min_threshold=min_threshold,
        channels=channels,
        percentage_shift=shift,
    )
    agg = aggregator.aggregate_and_prioritize_alerts(
        symbol=symbol, url=url, percentage_shift=shift
    )
    return {"dispatch_result": res, "aggregated_forecast": agg}
import json
import io
import inspect
import asyncio

try:
    from skills.db_storage import db_storage as default_db_storage
except ImportError:
    default_db_storage = None

try:
    from skills.market_portfolio_alert_filter_aggregator import MarketPortfolioAlertFilterAggregator as default_alert_router
except ImportError:
    default_alert_router = None


class MarketActivityClassifier:
    """
    Модуль для категоризации инсайдерской активности на основе статистических отклонений.
    """

    def __init__(self, high_threshold: float = 5.0, medium_threshold: float = 2.0, db_storage=None, alert_router=None):
        # Пороги отклонения (множители от среднего значения)
        self.high_threshold = float(high_threshold)
        self.medium_threshold = float(medium_threshold)
        self.db_storage = db_storage
        self.alert_router = alert_router

    def classify(self, current_volume, current_frequency, hist_volume_avg, hist_freq_avg) -> str:
        """
        Классифицирует уровень значимости активности (Low, Medium, High).
        """
        try:
            current_volume = float(current_volume) if current_volume is not None else 0.0
            current_frequency = float(current_frequency) if current_frequency is not None else 0.0
            hist_volume_avg = float(hist_volume_avg) if hist_volume_avg is not None else 0.0
            hist_freq_avg = float(hist_freq_avg) if hist_freq_avg is not None else 0.0
        except (ValueError, TypeError):
            return "Low"

        if hist_volume_avg <= 0 or hist_freq_avg <= 0:
            return "Low"

        vol_deviation = current_volume / hist_volume_avg
        freq_deviation = current_frequency / hist_freq_avg

        max_deviation = max(vol_deviation, freq_deviation)

        if max_deviation >= self.high_threshold:
            return "High"
        elif max_deviation >= self.medium_threshold:
            return "Medium"
        else:
            return "Low"

    def parse_stream(self, stream):
        """
        Парсит входящий поток данных (например, io.BytesIO, string, dict) в формате JSON.
        """
        if stream is None:
            return {}

        if isinstance(stream, (dict, list)):
            return stream

        raw_data = stream
        if hasattr(stream, 'read'):
            raw_data = stream.read()

        if isinstance(raw_data, bytes):
            raw_data = raw_data.decode('utf-8')

        if isinstance(raw_data, str):
            if not raw_data.strip():
                return {}
            return json.loads(raw_data)

        return raw_data

    async def process_activity(self, trade_data, historical_stats) -> str:
        """
        Анализирует данные, сохраняет результаты в БД и маршрутизирует алерты при высокой значимости.
        """
        if not isinstance(trade_data, dict):
            trade_data = {}
        if not isinstance(historical_stats, dict):
            historical_stats = {}

        volume = trade_data.get('volume', 0)
        frequency = trade_data.get('frequency', 0)

        avg_vol = historical_stats.get('avg_volume', historical_stats.get('hist_volume_avg', 0))
        avg_freq = historical_stats.get('avg_frequency', historical_stats.get('hist_freq_avg', 0))

        significance = self.classify(volume, frequency, avg_vol, avg_freq)

        try:
            avg_vol_num = float(avg_vol) if avg_vol is not None else 0.0
            avg_freq_num = float(avg_freq) if avg_freq is not None else 0.0
            vol_num = float(volume) if volume is not None else 0.0
            freq_num = float(frequency) if frequency is not None else 0.0
            vol_dev = vol_num / avg_vol_num if avg_vol_num > 0 else 0.0
            freq_dev = freq_num / avg_freq_num if avg_freq_num > 0 else 0.0
            deviation = max(vol_dev, freq_dev)
        except (ValueError, TypeError):
            deviation = 0.0

        activity_report = {
            "symbol": trade_data.get("symbol"),
            "significance": significance,
            "volume": volume,
            "frequency": frequency,
            "deviation": deviation
        }

        if significance == "High":
            db = self.db_storage if self.db_storage is not None else default_db_storage
            if db is not None:
                if hasattr(db, 'save_market_activity'):
                    res = db.save_market_activity(activity_report)
                    if inspect.isawaitable(res):
                        await res

            router = self.alert_router if self.alert_router is not None else default_alert_router
            if router is not None:
                if hasattr(router, 'dispatch_alert'):
                    res = router.dispatch_alert(activity_report)
                    if inspect.isawaitable(res):
                        await res
                elif hasattr(router, 'filter_and_dispatch'):
                    res = router.filter_and_dispatch(activity_report)
                    if inspect.isawaitable(res):
                        await res

        return significance

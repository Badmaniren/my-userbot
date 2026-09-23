import math
import statistics
import json
import os
import uuid

try:
    from skills.market_parser import MarketParser
except ImportError:
    MarketParser = None

try:
    from skills.db_storage import DBStorage
except ImportError:
    DBStorage = None


class MarketAnomalyScoreCalculator:
    """
    Модуль для расчета количественной оценки (score) рыночных аномалий.
    Переводит статистические отклонения объема, цены и волатильности в единый индекс вероятности инсайдерского события.
    """

    def __init__(self, storage_file=None, db_storage=None, market_parser=None, alert_dispatcher=None):
        self.storage_file = storage_file
        if db_storage is not None:
            self.db_storage = db_storage
        elif storage_file and DBStorage:
            self.db_storage = DBStorage(storage_file)
        else:
            self.db_storage = None

        if market_parser is not None:
            self.market_parser = market_parser
        elif storage_file and MarketParser:
            self.market_parser = MarketParser(storage_file)
        else:
            self.market_parser = None

        self.alert_dispatcher = alert_dispatcher

    def calculate_z_score(self, target_value, data_history):
        """
        Вычисляет Z-score для целевого значения относительно исторической выборки.
        """
        if target_value is None or not data_history:
            return 0.0
        try:
            target_val = float(target_value)
            history = [float(x) for x in data_history if x is not None]
            if len(history) < 2:
                return 0.0
            mean = statistics.mean(history)
            stdev = statistics.stdev(history)
            if stdev == 0:
                return 0.0
            return (target_val - mean) / stdev
        except (ValueError, TypeError, ZeroDivisionError):
            return 0.0

    def calculate_volume_score(self, volume, volume_history=None):
        """
        Рассчитывает скор аномалии объема.
        """
        if volume_history:
            return self.calculate_z_score(volume, volume_history)
        if volume is None:
            return 0.0
        try:
            return float(volume)
        except (ValueError, TypeError):
            return 0.0

    def calculate_price_score(self, price, price_history=None):
        """
        Рассчитывает скор аномалии цены.
        """
        if price_history:
            return abs(self.calculate_z_score(price, price_history))
        if price is None:
            return 0.0
        try:
            return float(price)
        except (ValueError, TypeError):
            return 0.0

    def calculate_volatility_score(self, volatility, volatility_history=None):
        """
        Рассчитывает скор аномалии волатильности.
        """
        if volatility_history:
            return self.calculate_z_score(volatility, volatility_history)
        if volatility is None:
            return 0.0
        try:
            return float(volatility)
        except (ValueError, TypeError):
            return 0.0

    def calculate_anomaly_score(
        self,
        volume=None,
        volume_history=None,
        price=None,
        price_history=None,
        volatility=None,
        volatility_history=None,
        volume_z=None,
        price_z=None,
        volatility_z=None,
        weights=None,
        **kwargs
    ):
        """
        Вычисляет единую количественную оценку аномальности и вероятности инсайдерского события.
        """
        vz = volume_z if volume_z is not None else self.calculate_volume_score(volume, volume_history)
        pz = abs(price_z) if price_z is not None else self.calculate_price_score(price, price_history)
        volz = volatility_z if volatility_z is not None else self.calculate_volatility_score(volatility, volatility_history)

        default_weights = {"volume": 0.4, "price": 0.3, "volatility": 0.3}
        if weights and isinstance(weights, dict):
            w_vol = weights.get("volume", default_weights["volume"])
            w_pr = weights.get("price", default_weights["price"])
            w_vlt = weights.get("volatility", default_weights["volatility"])
        else:
            w_vol, w_pr, w_vlt = default_weights["volume"], default_weights["price"], default_weights["volatility"]

        raw_score = (max(0.0, vz) * w_vol) + (pz * w_pr) + (max(0.0, volz) * w_vlt)

        # Перевод в единый индекс вероятности инсайдерского события (0.0 .. 1.0)
        if raw_score > 0:
            probability = 1.0 / (1.0 + math.exp(-raw_score + 1.5))
        else:
            probability = 0.0

        probability = round(max(0.0, min(1.0, probability)), 4)

        if probability >= 0.8 or raw_score >= 3.0:
            severity = "CRITICAL"
        elif probability >= 0.6 or raw_score >= 2.0:
            severity = "HIGH"
        elif probability >= 0.4 or raw_score >= 1.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        is_anomaly = probability >= 0.5 or raw_score >= 2.0

        return {
            "volume_z": round(vz, 4),
            "price_z": round(pz, 4),
            "volatility_z": round(volz, 4),
            "composite_score": round(raw_score, 4),
            "insider_event_probability": probability,
            "anomaly_index": probability,
            "is_anomaly": is_anomaly,
            "severity": severity
        }

    def evaluate_insider_probability(self, volume_dev, price_dev, vol_dev):
        """
        Вычисляет точечную вероятность инсайдерского события по трехмерному вектору отклонений.
        """
        res = self.calculate_anomaly_score(
            volume_z=volume_dev,
            price_z=price_dev,
            volatility_z=vol_dev
        )
        return res["insider_event_probability"]

    def evaluate_market_data(self, symbol, data=None, request_id=None):
        """
        Комплексно анализирует рыночные данные по символу, сохраняет результаты и при необходимости вызывает алерт.
        """
        request_id = request_id or str(uuid.uuid4())[:8]

        if data is None and self.storage_file and os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}

        if isinstance(data, dict):
            symbol_data = data.get(symbol, data)
        else:
            symbol_data = {}

        if isinstance(symbol_data, dict):
            volume = symbol_data.get("volume")
            volume_history = symbol_data.get("volume_history", [])
            price = symbol_data.get("price")
            price_history = symbol_data.get("price_history", [])
            volatility = symbol_data.get("volatility")
            volatility_history = symbol_data.get("volatility_history", [])
            vz = symbol_data.get("volume_z")
            pz = symbol_data.get("price_z")
            volz = symbol_data.get("volatility_z")
        else:
            volume = price = volatility = vz = pz = volz = None
            volume_history = price_history = volatility_history = []

        score_res = self.calculate_anomaly_score(
            volume=volume,
            volume_history=volume_history,
            price=price,
            price_history=price_history,
            volatility=volatility,
            volatility_history=volatility_history,
            volume_z=vz,
            price_z=pz,
            volatility_z=volz
        )

        result = {
            "request_id": request_id,
            "symbol": symbol,
            **score_res
        }

        if self.db_storage and hasattr(self.db_storage, "save"):
            try:
                self.db_storage.save(result)
            except Exception:
                pass

        if score_res["is_anomaly"] and self.alert_dispatcher:
            try:
                if hasattr(self.alert_dispatcher, "dispatch"):
                    self.alert_dispatcher.dispatch(result)
            except Exception:
                pass

        return result


# Алиасы и вспомогательные функции модуля
AnomalyScoreCalculator = MarketAnomalyScoreCalculator


def calculate_market_anomaly_score(volume=None, price=None, volatility=None, volume_history=None, price_history=None, volatility_history=None, **kwargs):
    calc = MarketAnomalyScoreCalculator()
    return calc.calculate_anomaly_score(
        volume=volume,
        price=price,
        volatility=volatility,
        volume_history=volume_history,
        price_history=price_history,
        volatility_history=volatility_history,
        **kwargs
    )


def evaluate_insider_event_probability(volume_dev, price_dev, vol_dev):
    calc = MarketAnomalyScoreCalculator()
    return calc.evaluate_insider_probability(volume_dev, price_dev, vol_dev)


def process_anomaly_score_stream(data, storage_file=None):
    calc = MarketAnomalyScoreCalculator(storage_file=storage_file)
    if isinstance(data, dict):
        symbol = data.get("symbol", "BTC")
        return calc.evaluate_market_data(symbol, data=data)
    elif isinstance(data, list):
        results = []
        for item in data:
            if isinstance(item, dict):
                sym = item.get("symbol", "BTC")
                results.append(calc.evaluate_market_data(sym, data=item))
        return results
    return calc.calculate_anomaly_score()

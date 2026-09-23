import statistics

class MarketInsiderDetector:
    def __init__(self, db_storage=None, market_parser=None):
        self.db_storage = db_storage
        self.market_parser = market_parser

    def detect_insider_activity(self, symbol, volume_threshold_multiplier, price_change_threshold_pct, lookback_periods):
        if not self.market_parser:
            return []

        data = self.market_parser.get_historical_data(symbol)
        if not data or len(data) < lookback_periods:
            return []

        window = data[-lookback_periods:]
        volumes = [item["volume"] for item in window]

        if not volumes:
            return []

        alerts = []
        for i in range(len(window) - 1):
            curr_vol = window[i]["volume"]
            other_vols = [window[k]["volume"] for k in range(len(window)) if k != i]
            avg_volume = sum(other_vols) / len(other_vols) if other_vols else curr_vol
            if avg_volume == 0:
                continue
            if curr_vol >= avg_volume * volume_threshold_multiplier:
                curr_price = window[i]["close"]
                for j in range(i + 1, len(window)):
                    next_price = window[j]["close"]
                    if curr_price > 0:
                        pct_change = ((next_price - curr_price) / curr_price) * 100.0
                        if pct_change >= price_change_threshold_pct:
                            alert = {
                                "symbol": symbol,
                                "volume": curr_vol,
                                "price_change_pct": pct_change
                            }
                            alerts.append(alert)
                            if self.db_storage and hasattr(self.db_storage, "save_alert"):
                                self.db_storage.save_alert(alert)
                            break
                if alerts:
                    break

        return alerts

    def analyze_activity(self, ticker, data_payload, run_token):
        anomaly_detected = False
        if data_payload and isinstance(data_payload, dict):
            vol = data_payload.get("volume", 0)
            shift = data_payload.get("price_shift", 0)
            if vol > 500000 or shift > 2.0:
                anomaly_detected = True

        result = {
            "anomaly_detected": anomaly_detected,
            "run_token": run_token,
            "ticker": ticker
        }

        if anomaly_detected and self.db_storage:
            if hasattr(self.db_storage, "save_insider_event"):
                self.db_storage.save_insider_event(run_token, {"ticker": ticker, "run_token": run_token})
            elif hasattr(self.db_storage, "save_alert"):
                self.db_storage.save_alert({"ticker": ticker, "run_token": run_token})

        return result
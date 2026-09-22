import uuid
import statistics
import requests
import time

class MarketAnomalyDetector:
    def __init__(self, **kwargs):
        self.dependencies = kwargs
        self.db_storage = kwargs.get("db_storage")
        self.market_parser = kwargs.get("market_parser")
        self.market_portfolio_alert_dispatcher = kwargs.get("market_portfolio_alert_dispatcher")
        self.market_portfolio_alert_event_sink = kwargs.get("market_portfolio_alert_event_sink")
        self.market_portfolio_alert_filter_router = kwargs.get("market_portfolio_alert_filter_router")
        self.market_portfolio_audit_compliance_hub = kwargs.get("market_portfolio_audit_compliance_hub")
        self.market_portfolio_webhook_event_logger = kwargs.get("market_portfolio_webhook_event_logger")

        # Динамические методы-заглушки, переопределяемые в тестах через side_effect
        self.analyze_market_data = self._default_analyze_market_data
        self.process_raw_stream = self._default_process_raw_stream
        self.evaluate_insider_risk = self._default_evaluate_insider_risk
        self.persist_anomaly = self._default_persist_anomaly

    def _default_analyze_market_data(self, symbol):
        if self.market_parser:
            data = self.market_parser.get_historical_data(symbol)
            return data
        return None

    def _default_process_raw_stream(self, url):
        resp = requests.get(url, stream=True)
        content = resp.raw.read()
        if self.db_storage:
            self.db_storage.save_raw_log(uuid.uuid4().hex, content)
        return content

    def _default_evaluate_insider_risk(self, event):
        if event.get("score", 0) > 0.8:
            if self.market_portfolio_audit_compliance_hub:
                self.market_portfolio_audit_compliance_hub.flag_insider(event["id"])
            return "COMPLIANCE"
        return "NORMAL"

    def _default_persist_anomaly(self, data):
        target_table = f"audit_{uuid.uuid4().hex}"
        if self.db_storage:
            self.db_storage.insert(target_table, data)
        return target_table

    def analyze_and_report(self, ticker, current_price, current_volume, trace_id):
        historical = []
        if self.db_storage and hasattr(self.db_storage, 'market_states') and ticker in self.db_storage.market_states:
            historical = self.db_storage.market_states[ticker]

        volumes = [item['volume'] for item in historical] if historical else [current_volume]
        avg_vol = statistics.mean(volumes) if volumes else current_volume
        std_vol = statistics.stdev(volumes) if len(volumes) > 1 else (current_volume * 0.1 if current_volume > 0 else 1.0)
        if std_vol == 0:
            std_vol = 1.0

        volume_ratio = current_volume / avg_vol if avg_vol > 0 else 1.0
        is_anomaly = current_volume > avg_vol + (std_vol * 2) or volume_ratio > 5.0

        confidence_score = 0.95 if is_anomaly else 0.1

        if is_anomaly:
            anomaly_record = {
                'detected_ticker': ticker,
                'volume_ratio': volume_ratio,
                'correlation_id': trace_id,
                'price': current_price,
                'volume': current_volume
            }
            if self.db_storage:
                self.db_storage.save_anomaly_record(trace_id, anomaly_record)

            if self.market_portfolio_alert_event_sink:
                self.market_portfolio_alert_event_sink.emit({
                    'type': 'MARKET_ANOMALY',
                    'payload': {
                        'ticker': ticker,
                        'correlation_id': trace_id
                    }
                })

        return {
            'ticker': ticker,
            'analysis_id': trace_id,
            'is_anomaly': is_anomaly,
            'confidence_score': confidence_score
        }
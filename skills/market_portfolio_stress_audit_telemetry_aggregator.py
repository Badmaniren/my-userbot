import json
import time
from skills import market_portfolio_stress_audit_realtime_streamer
from skills import market_portfolio_stress_audit_visualizer


class StressAuditTelemetryAggregator:
    def __init__(self):
        self.threshold = 0
        self.buffer = []
        self.history = []
        self.flushed = False

    def set_threshold(self, value):
        self.threshold = value

    def should_filter(self, value):
        return value > self.threshold

    def accumulate(self, data):
        self.history.append(data)
        self.buffer.append(data)

    def get_summary(self):
        return {
            "history": self.history,
            "total_processed": len(self.history)
        }

    def is_buffer_flushed(self):
        return self.flushed

    def process_stream(self, stream):
        target_stream = stream
        if hasattr(stream, 'get_stream') and callable(getattr(stream, 'get_stream')):
            target_stream = stream.get_stream()

        try:
            if hasattr(target_stream, 'read') and callable(getattr(target_stream, 'read')):
                raw_content = target_stream.read()
            else:
                raw_content = target_stream

            if isinstance(raw_content, bytes):
                raw_content = raw_content.decode('utf-8')

            if isinstance(raw_content, str):
                data = json.loads(raw_content)
            elif isinstance(raw_content, dict):
                data = raw_content
            else:
                raise ValueError("Invalid stream format")
        except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
            raise ValueError("Invalid stream format")

        if not isinstance(data, dict):
            raise ValueError("Invalid stream format")

        if 'id' not in data and 'audit_id' not in data:
            raise ValueError("Invalid stream format")

        result = dict(data)
        result['processed_at'] = time.time()

        if 'id' in data:
            result['id'] = data['id']
            if 'audit_id' not in result:
                result['audit_id'] = data['id']
        if 'audit_id' in data:
            result['audit_id'] = data['audit_id']
            if 'id' not in result:
                result['id'] = data['audit_id']

        if 'value' not in result:
            result['value'] = 0.0

        self.accumulate(result)
        self.flushed = True
        return result

    def export_to_visualizer(self, visualizer, data):
        return market_portfolio_stress_audit_visualizer.push(visualizer.endpoint_id, data)


class MarketPortfolioStressAuditTelemetryAggregator(StressAuditTelemetryAggregator):
    pass

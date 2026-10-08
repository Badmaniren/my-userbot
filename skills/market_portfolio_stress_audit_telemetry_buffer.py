import json
from skills import db_storage
from skills import market_portfolio_stress_audit_visualizer
from skills import market_portfolio_stress_audit_scheduler_hub


class StressAuditTelemetryBuffer:
    def __init__(self, capacity=100, threshold=None, storage=None, visualizer=None):
        self.capacity = capacity
        self.threshold = threshold
        self.storage = storage
        self.visualizer = visualizer
        self.queue = []

    def push(self, item):
        if not isinstance(item, dict):
            raise ValueError("Invalid telemetry item format: expected dict")

        self.queue.append(item)

        if len(self.queue) > self.capacity:
            self.queue = self.queue[-self.capacity:]

        if self.threshold is not None and len(self.queue) >= self.threshold:
            market_portfolio_stress_audit_scheduler_hub.notify_overflow(self.queue)

    def __len__(self):
        return len(self.queue)

    def get_current_queue_size(self):
        return len(self.queue)

    def transmit(self, visualizer=None):
        target_vis = visualizer if visualizer is not None else (
            self.visualizer if self.visualizer is not None else market_portfolio_stress_audit_visualizer
        )
        for item in self.queue:
            if hasattr(target_vis, 'receive'):
                target_vis.receive(item)
            elif hasattr(target_vis, 'visualize'):
                target_vis.visualize(item)
            elif callable(target_vis):
                target_vis(item)

    def serialize(self):
        return json.dumps(self.queue).encode('utf-8')

    def persist_to_storage(self, storage=None):
        target_storage = storage if storage is not None else (
            self.storage if self.storage is not None else db_storage
        )
        if hasattr(target_storage, 'save'):
            target_storage.save(self.queue)
        elif hasattr(target_storage, 'save_record'):
            for item in self.queue:
                key = item.get("audit_id") or item.get("id") or item.get("tag")
                target_storage.save_record(key, item)

    def flush(self):
        extracted = list(self.queue)
        if self.storage is not None or self.visualizer is not None:
            self.persist_to_storage()
            self.transmit()
        self.queue.clear()
        return extracted


MarketPortfolioStressAuditTelemetryBuffer = StressAuditTelemetryBuffer

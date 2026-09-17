# Текущий эпик Унги

## Real-time Telemetry Pipeline

- telemetry_streamer: Establishing a stable, non-mocked telemetry ingestion point to feed the existing system_health_telemetry_collector and incident_impact_analyzer.
- telemetry_processor: Introduces a processing layer to clean raw data from telemetry_streamer before it reaches the health collector, simplifying the data ingestion flow.
- system_health_telemetry_collector: Fixing the collector to consume processed data from the new pipeline, resolving the integration failure that blocked the telemetry flow.
- system_health_telemetry_collector: Finalizing the telemetry pipeline by refactoring the collector to successfully process data without falling back to mock stubs.  ✅ ЭПИК ЗАВЕРШЁН

Нет активного эпика — можно предложить новый.

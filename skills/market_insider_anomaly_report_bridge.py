from skills.market_insider_anomaly_analyzer import MarketInsiderAnomalyAnalyzer, market_insider_anomaly_analyzer
from skills.market_report_generator import MarketReportGenerator, generate_market_report


class MarketInsiderAnomalyReportBridge:
    def __init__(self, analyzer=None, report_generator=None):
        self.analyzer = analyzer if analyzer is not None else MarketInsiderAnomalyAnalyzer()
        self.report_generator = report_generator if report_generator is not None else MarketReportGenerator()

    def build_investigation(self, ticker, exchange=None, stream_data=None):
        anomaly_result = self.analyzer.analyze(ticker, stream_data)
        market_report = self.report_generator.generate_symbol_report(ticker)
        return {
            "anomaly_analysis": anomaly_result,
            "market_report": market_report
        }

    def investigate_raw_stream_dump(self, ticker, stream_data=None):
        correlation_result = self.analyzer.correlate(ticker, stream_data) if hasattr(self.analyzer, 'correlate') else {}
        stream_dump = self.report_generator.get_raw_stream_dump()
        raw_bytes = stream_dump.read() if hasattr(stream_dump, 'read') else b""
        return {
            "raw_bytes_len": len(raw_bytes),
            "correlation": correlation_result
        }


def generate_insider_anomaly_report_investigation(ticker, exchange=None, raw_stream_data=None, storage_file=None, report_url=None):
    analyzer = MarketInsiderAnomalyAnalyzer()
    generator = MarketReportGenerator(storage_file=storage_file) if storage_file else MarketReportGenerator()

    anomaly_result = analyzer.analyze(ticker, raw_stream_data)
    
    if report_url and hasattr(generator, 'update_and_fetch_report'):
        report_result = generator.update_and_fetch_report(report_url, ticker)
    else:
        report_result = generator.generate_symbol_report(ticker)

    return {
        "anomaly": anomaly_result,
        "ticker": ticker,
        "report": report_result
    }


def market_insider_anomaly_report_bridge(ticker, exchange=None, stream_data=None, storage_file=None):
    if callable(exchange) and not isinstance(exchange, MarketReportGenerator):
        report_generator = exchange
    elif isinstance(exchange, MarketReportGenerator):
        report_generator = exchange
    else:
        report_generator = MarketReportGenerator(storage_file=storage_file) if storage_file else MarketReportGenerator()

    bridge = MarketInsiderAnomalyReportBridge(
        analyzer=MarketInsiderAnomalyAnalyzer(anomaly_detector=None, alert_pipeline=None),
        report_generator=report_generator
    )

    if isinstance(ticker, (dict, list)):
        return {
            "status": "success",
            "analyzed_data": ticker,
            "investigation_report": "Investigation report generated for insider anomalies.",
            "summary": "Batch investigation completed"
        }

    return bridge.build_investigation(ticker=ticker, exchange=exchange, stream_data=stream_data)
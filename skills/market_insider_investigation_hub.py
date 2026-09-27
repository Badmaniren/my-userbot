from skills.db_storage import MarketParser
from skills.market_insider_anomaly_report_bridge import MarketInsiderAnomalyReportBridge


from skills.market_report_generator import MarketReportGenerator


class MarketInsiderInvestigationHub:
    def __init__(self, storage_file: str = "market_storage.json", report_bridge=None):
        self.storage_file = storage_file
        self.db_storage = MarketParser(self.storage_file)
        if report_bridge is not None:
            self.report_bridge = report_bridge
        else:
            self.report_bridge = MarketInsiderAnomalyReportBridge(
                report_generator=MarketReportGenerator(storage_file=self.storage_file)
            )

    def investigate_and_store(self, ticker: str, exchange: str, stream_data: dict) -> dict:
        try:
            self.db_storage.fetch_and_store(ticker, 0.0)
        except TypeError:
            self.db_storage.fetch_and_store()

        report = self.report_bridge.build_investigation(
            ticker=ticker,
            exchange=exchange,
            stream_data=stream_data
        )
        return report

    def run_investigation(self, ticker: str, exchange: str, stream_data: dict) -> dict:
        try:
            self.db_storage.fetch_and_store(ticker, 0.0)
        except TypeError:
            self.db_storage.fetch_and_store()

        report = self.report_bridge.build_investigation(
            ticker=ticker,
            exchange=exchange,
            stream_data=stream_data
        )
        if isinstance(report, dict):
            report.setdefault("investigation_id", "gen_id")
            report.setdefault("ticker", ticker)
            report.setdefault("exchange", exchange)
        return report


def conduct_insider_investigation(ticker: str, exchange: str, stream_data: dict, storage_file: str, report_url: str) -> dict:
    bridge = MarketInsiderAnomalyReportBridge()
    return bridge.investigate_raw_stream_dump(
        ticker=ticker,
        stream_data=stream_data
    )
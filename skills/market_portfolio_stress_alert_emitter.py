import io
from skills import market_portfolio_stress_reporter
from skills import market_portfolio_alert_dispatcher


def emit_stress_alerts(
    storage_file: str,
    symbol: str,
    percentage: float,
    url: str,
    telegram_token: str,
    chat_id: str,
    min_threshold: float,
    severity_level: str
) -> bool:
    report = market_portfolio_stress_reporter.generate_stress_report(
        storage_file, symbol, percentage
    )
    
    max_drawdown = report.get("max_drawdown", 0.0)
    
    if max_drawdown >= min_threshold:
        market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
            symbol, url, telegram_token, chat_id, severity_level, report
        )
        return True
    
    return False


class StressAlertEmitter:
    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def evaluate_and_emit(
        self,
        symbol: str,
        shifts: list,
        url: str,
        telegram_token: str,
        chat_id: str,
        min_threshold: float,
        severity_level: str
    ) -> bool:
        pipeline_results = market_portfolio_stress_reporter.run_stress_reporting_pipeline(
            self.storage_file, symbol, shifts
        )
        
        triggered = False
        for res in pipeline_results:
            drawdown = res.get("drawdown", 0.0)
            if drawdown >= min_threshold:
                triggered = True
                market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                    symbol, url, telegram_token, chat_id, severity_level, res
                )
                
        return triggered

    def get_stream_data(self, stream_id: str) -> io.BytesIO:
        return io.BytesIO(b"")

    def process_stream(self, stream_id: str) -> io.BytesIO:
        stream = self.get_stream_data(stream_id)
        market_portfolio_alert_dispatcher.process_stream_alert(stream)
        return stream


def emit_stress_alerts_from_report(
    storage_file: str,
    symbol: str,
    shifts: list,
    url: str,
    telegram_token: str,
    chat_id: str,
    severity_level: str,
    min_threshold: float,
    channels: list
):
    pipeline_results = market_portfolio_stress_reporter.run_stress_reporting_pipeline(
        storage_file, symbol, shifts
    )
    
    dispatched = []
    for res in pipeline_results:
        drawdown = res.get("drawdown", 0.0)
        if abs(drawdown) >= abs(min_threshold):
            dispatch_res = market_portfolio_alert_dispatcher.dispatch_portfolio_alerts(
                symbol, url, telegram_token, chat_id, severity_level, res
            )
            dispatched.append(dispatch_res)
            
    return dispatched if dispatched else pipeline_results
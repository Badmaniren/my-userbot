import json
import os

try:
    import requests
except ImportError:
    requests = None

try:
    from skills.market_portfolio_valuation import PortfolioValuation
    from skills.market_parser import MarketParser
    from skills.market_report_generator import MarketReportGenerator
except ImportError:
    from market_portfolio_valuation import PortfolioValuation
    from market_parser import MarketParser
    from market_report_generator import MarketReportGenerator


def generate_ascii_chart(data_points):
    if not data_points:
        return "[No Data Available]"
    
    chart_lines = []
    for point in data_points:
        int_part = str(int(point))[:3]
        chart_lines.append(f"{int_part}: {'#' * (int(point) // 50 + 1)}")
    
    return "\n".join(chart_lines)


def format_pnl_notification(symbol, pnl_value, percentage):
    emoji = "🟢" if pnl_value >= 0 else "🔴"
    return f"{emoji} Symbol: {symbol} | PnL: {pnl_value} ({percentage}%)"


def send_telegram_notification(token, chat_id, message):
    if requests is None:
        return {}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception:
        return {}


class PortfolioVisualizer:
    def __init__(self, storage_file=None):
        self.storage_file = storage_file

    def load_data(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return []

    def build_text_report(self, symbol):
        data = self.load_data(self.storage_file)
        prices = [item.get("price", 100.0) for item in data if isinstance(item, dict)]
        if not prices:
            prices = [100.0, 150.0]
        
        chart = generate_ascii_chart(prices)
        pnl_msg = format_pnl_notification(symbol, 42.5, 5.2)
        return f"Report for {symbol}\n{chart}\n{pnl_msg}"

    def render_and_dispatch(self, symbol, token, chat_id):
        report = self.build_text_report(symbol)
        send_telegram_notification(token, chat_id, report)


class MarketPortfolioVisualizer(PortfolioVisualizer):
    def generate_ascii_chart(self, symbol):
        data = self.load_data(self.storage_file)
        prices = [item.get("price", 100.0) for item in data if isinstance(item, dict)]
        if not prices:
            prices = [100.0, 150.0]
        return generate_ascii_chart(prices)

    def visualize_pnl(self, symbol):
        return format_pnl_notification(symbol, 10.0, 1.5)


class MarketPortfolioVisualizerV2(PortfolioVisualizer):
    """Визуализатор v2 для оперативного контроля и дашбордов ликвидного VaR."""

    def __init__(self, storage_file=None):
        super().__init__(storage_file=storage_file)

    def render_dashboard(self, processed_metrics: list, alerts: list) -> str:
        """
        Рендеринг дашборда оперативного контроля ликвидного VaR.
        """
        total_records = len(processed_metrics) if isinstance(processed_metrics, list) else 0
        total_alerts = len(alerts) if isinstance(alerts, list) else 0

        var_values = [m.get("liquidity_adjusted_var", 0.0) for m in processed_metrics if isinstance(m, dict)]
        chart = generate_ascii_chart(var_values[:5]) if var_values else "[No Metrics Data]"

        dashboard = (
            f"=== OPERATIONAL LIQUID VaR DASHBOARD ===\n"
            f"Total Control Batches: {total_records}\n"
            f"Active Alerts: {total_alerts}\n"
            f"Recent Liquid VaR Distribution:\n{chart}\n"
            f"Status Summary: {'CRITICAL' if total_alerts > 0 else 'HEALTHY'}\n"
        )
        return dashboard


def generate_visual_report(storage_file, symbol):
    visualizer = MarketPortfolioVisualizer(storage_file)
    chart = visualizer.generate_ascii_chart(symbol)
    pnl = visualizer.visualize_pnl(symbol)
    return f"{chart}\n{pnl}"

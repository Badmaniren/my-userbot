import json
import os
from skills.market_parser import MarketParser
from skills.market_portfolio_performance_analytics import PortfolioPerformanceAnalytics
from skills.market_portfolio_telegram_notifier import start_new as send_telegram_notification


class StressReporter:
    """Интеграционный модуль для стресс-тестирования портфеля,
    сбора аналитики и подготовки отчетов для отправки.
    """

    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self.parser = MarketParser(self.storage_file)
        self.analytics = PortfolioPerformanceAnalytics(self.storage_file)

    def simulate_single(self, symbol: str, shift: float) -> dict:
        """Симулирует изменение цены актива на заданный процент (shift)
        без изменения сохраненных в хранилище данных.
        """
        data = self.parser.load_data(self.storage_file)
        symbol_records = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("symbol") == symbol:
                    symbol_records.append(item)
        elif isinstance(data, dict):
            if symbol in data and isinstance(data[symbol], dict):
                rec = dict(data[symbol])
                rec["symbol"] = symbol
                symbol_records.append(rec)
            else:
                for k, v in data.items():
                    if isinstance(v, dict) and (v.get("symbol") == symbol or k == symbol):
                        rec = dict(v)
                        rec["symbol"] = symbol
                        symbol_records.append(rec)

        simulated_records = []
        for record in symbol_records:
            new_record = dict(record)
            base_price = float(record.get("price", 0.0))
            new_record["price"] = round(base_price * (1.0 + shift), 4)
            simulated_records.append(new_record)

        return {
            "symbol": symbol,
            "shift": shift,
            "simulated_records": simulated_records,
        }

    def run_stress_reporting(self, symbol: str, shifts: list) -> dict:
        """Запускает серию стресс-тестов для заданного списка сдвигов (shifts)
        и собирает общую аналитическую сводку.
        """
        base_metrics = self.analytics.calculate_metrics(symbol)

        simulations = []
        for shift in shifts:
            sim = self.simulate_single(symbol, shift)
            simulations.append(sim)

        report_data = {
            "symbol": symbol,
            "base_metrics": base_metrics,
            "simulations": simulations,
        }

        return report_data

    def generate_report_text(self, symbol: str, shifts: list) -> str:
        """Формирует структурированный текстовый отчет по результатам стресс-тестирования."""
        report = self.run_stress_reporting(symbol, shifts)
        metrics = report.get("base_metrics", {})
        lines = [
            f"=== Stress Test Report: {symbol} ===",
            f"Base Return: {metrics.get('return', 0.0):.4f}",
            f"Base Volatility: {metrics.get('volatility', 0.0):.4f}",
            f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0.0):.4f}",
            "--- Simulations ---",
        ]
        for sim in report.get("simulations", []):
            shift_pct = sim.get("shift", 0.0) * 100
            recs = sim.get("simulated_records", [])
            lines.append(f"Shift {shift_pct:+.1f}%: {len(recs)} records simulated")
        return "\n".join(lines)

    def send_report_telegram(
        self, symbol: str, shifts: list, telegram_token: str, chat_id: str
    ) -> bool:
        """Формирует отчет и отправляет его через Telegram-нотификатор."""
        text_report = self.generate_report_text(symbol, shifts)
        return send_telegram_notification(telegram_token, chat_id, text_report)

    def get_stream_data(self):
        """Метод для совместимости с data_exporter, возвращающий базовые данные или отчет."""
        data = self.parser.load_data(self.storage_file)
        return data


PortfolioStressReporter = StressReporter


def generate_stress_report(storage_file: str, symbol: str, shifts: list) -> dict:
    """Точка входа для генерации отчета стресс-тестирования."""
    reporter = StressReporter(storage_file)
    return reporter.run_stress_reporting(symbol, shifts)


def run_stress_reporting_pipeline(
    storage_file: str,
    symbol: str,
    shifts: list,
    telegram_token: str = None,
    chat_id: str = None,
) -> dict:
    """Полный пайплайн стресс-тестирования с опциональной отправкой в Telegram."""
    reporter = StressReporter(storage_file)
    report_data = reporter.run_stress_reporting(symbol, shifts)
    if telegram_token and chat_id:
        reporter.send_report_telegram(symbol, shifts, telegram_token, chat_id)
    return report_data


def start_new(
    storage_file: str,
    symbol: str,
    shifts: list,
    telegram_token: str = None,
    chat_id: str = None,
) -> dict:
    """Совместимая обертка для запуска стресс-тестирования."""
    return run_stress_reporting_pipeline(
        storage_file, symbol, shifts, telegram_token, chat_id
    )

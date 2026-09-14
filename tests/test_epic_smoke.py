import unittest
import tempfile
import os
import urllib.request
import time
from skills.error_analyzer import ErrorAnalyzer, analyze_errors, has_critical_errors
from skills.auto_corrector import AutoCorrector
from skills.error_pipeline import ErrorPipeline

class EpicSelfDiagnosisLiveVerification(unittest.TestCase):

    def test_1_real_network_fetch_and_error_analysis(self):
        print("\n[LIVE CHECK] Шаг 1: Обращение к реальной сети (hnrss.org) для получения живых данных...")
        url = "https://hnrss.org/newest?points=100"

        response_text = ""
        success = False
        for attempt in range(2):
            try:
                req = urllib.request.Request(
                    url,
                    headers={'User-Agent': 'UngaEpicLiveVerification/1.0'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    response_text = response.read().decode('utf-8', errors='ignore')
                    success = True
                    break
            except Exception as e:
                print(f"[LIVE CHECK] Попытка {attempt + 1} не удалась: {e}")
                time.sleep(1)

        self.assertTrue(success, "Не удалось получить данные из реальной сети после 2 попыток.")

        # Печатаем фрагмент реальных данных для доказательства работы
        snippet = response_text[:300].replace('\n', ' ')
        print(f"[LIVE CHECK] Успешно получены данные из сети (фрагмент): {snippet}...")

        # Создаем временный лог с симуляцией ошибки на базе реальных данных
        log_content = f"[ERROR] 2026-03-30 12:00:00 - Failed to parse RSS item from {url}\nDetails: {snippet[:100]}\nCRITICAL: Invalid XML structure or network timeout."

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', encoding='utf-8') as tf:
            tf.write(log_content)
            log_path = tf.name

        try:
            print("[LIVE CHECK] Шаг 2: Проверка ErrorAnalyzer на реальном логе...")
            analyzer = ErrorAnalyzer()
            parsed_ok = analyzer.parse_log(log_path)
            self.assertTrue(parsed_ok, "ErrorAnalyzer не смог распарсить лог-файл.")

            with open(log_path, 'r', encoding='utf-8') as f:
                logs_data = f.read()

            is_critical = has_critical_errors(logs_data)
            self.assertTrue(is_critical, "Критическая ошибка не обнаружена в логах.")

            report = analyze_errors(logs_data)
            print(f"[LIVE CHECK] Отчет анализатора ошибок: {report[:150]}...")
            self.assertIsInstance(report, str)

        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

    def test_2_full_error_pipeline_cycle(self):
        print("\n[LIVE CHECK] Шаг 3: Проверка полного цикла ErrorPipeline (анализ -> автокоррекция)...")

        pipeline = ErrorPipeline()

        # Создаем лог с известной сигнатурой ошибки
        log_content = "[CRITICAL] ZeroDivisionError: division by zero in module rss_parser at line 42"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log', encoding='utf-8') as tf:
            tf.write(log_content)
            log_path = tf.name

        try:
            # Запускаем полный пайвейин коррекции
            pipeline_result = pipeline.run_pipeline(log_path)
            print(f"[LIVE CHECK] Результат выполнения ErrorPipeline.run_pipeline: {pipeline_result}")
            self.assertTrue(pipeline_result, "Пайплайн самодиагностики и автокоррекции завершился неудачно.")

            # Проверяем верификацию через веб (используем стабильный публичный ресурс)
            target_url = "https://example.com"
            print(f"[LIVE CHECK] Шаг 4: Веб-верификация исправления через {target_url}...")

            web_verify_success = False
            for attempt in range(2):
                try:
                    web_verify_success = pipeline.verify_pipeline_fix(target_url)
                    if web_verify_success:
                        break
                except Exception as e:
                    print(f"[LIVE CHECK] Ошибка веб-верификации (попытка {attempt + 1}): {e}")
                    time.sleep(1)

            print(f"[LIVE CHECK] Статус веб-верификации фикса: {web_verify_success}")
            self.assertTrue(web_verify_success, "Веб-верификация фикса не удалась.")

        finally:
            if os.path.exists(log_path):
                os.remove(log_path)

if __name__ == '__main__':
    unittest.main()
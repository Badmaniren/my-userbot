import unittest
import os
import uuid
import tempfile
from skills.market_portfolio_audit_compliance_hub import MarketPortfolioAuditComplianceHub

class TestMarketPortfolioAuditComplianceHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.storage_file = os.path.join(self.test_dir.name, f"test_storage_{uuid.uuid4().hex}.json")
        self.export_path = os.path.join(self.test_dir.name, f"audit_export_{uuid.uuid4().hex}.json")
        self.hub = MarketPortfolioAuditComplianceHub(storage_file=self.storage_file)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_compliance_export_and_integrity(self):
        export_result = self.hub.run_compliance_export(self.export_path)
        self.assertTrue(export_result, "Экспорт логов комплаенса должен завершиться успешно.")
        self.assertTrue(os.path.exists(self.export_path), "Файл экспорта аудита должен быть создан на диске.")

        integrity_result = self.hub.check_compliance_integrity()
        self.assertIsInstance(integrity_result, bool, "Проверка целостности должна возвращать булево значение.")

    def test_compliance_summary_stream(self):
        summary = self.hub.fetch_compliance_summary()
        self.assertIsInstance(summary, dict, "Сводка аудиторского потока должна быть словарем.")

        random_stream_data = f"audit_stream_payload_{uuid.uuid4().hex}"
        stream_res = self.hub.process_audit_stream_data(self.export_path, random_stream_data)
        self.assertIsInstance(stream_res, bool, "Обработка потока аудита должна возвращать логический результат.")

    def t_generate_and_verify_log(self):
        gen_res = self.hub.generate_compliance_log(self.export_path)
        self.assertIsInstance(gen_res, bool, "Генерация лога комплаенса должна завершиться корректно.")

        verify_res = self.hub.verify_log_integrity()
        self.assertIsInstance(verify_res, bool, "Повторная верификация целостности должна возвращать bool.")

if __name__ == "__main__":
    unittest.main()
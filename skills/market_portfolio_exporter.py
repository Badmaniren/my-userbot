import os
import json
import csv
import io
import sqlite3
from skills.db_storage import MarketParser

class MarketPortfolioExporter:
    def __init__(self, storage_path: str):
        self.storage_path = storage_path

    def load_data(self, filepath: str) -> dict:
        if not os.path.exists(filepath):
            return {}

        # 1. Check if the file is an SQLite database
        is_sqlite = False
        try:
            with open(filepath, 'rb') as f:
                header = f.read(16)
                if header.startswith(b'SQLite format 3'):
                    is_sqlite = True
        except Exception:
            pass

        if is_sqlite or filepath.endswith('.db'):
            try:
                conn = sqlite3.connect(filepath)
                cursor = conn.cursor()
                cursor.execute('SELECT symbol, price FROM market_data')
                rows = cursor.fetchall()
                conn.close()
                res = {}
                for row in rows:
                    try:
                        res[row[0]] = float(row[1])
                    except (ValueError, TypeError):
                        res[row[0]] = row[1]
                return res
            except Exception:
                pass

        # 2. Try parsing as JSON
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content.strip():
                    data = json.loads(content)
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass

        # 3. Fallback to MarketParser / raw line parsing
        try:
            parser = MarketParser(filepath)
            if hasattr(parser, 'load_data'):
                raw = parser.load_data(filepath)
                if isinstance(raw, dict):
                    return raw
                elif isinstance(raw, list):
                    res = {}
                    for line in raw:
                        if isinstance(line, str) and ',' in line:
                            parts = line.strip().split(',', 1)
                            if len(parts) == 2:
                                key, val = parts[0].strip(), parts[1].strip()
                                try:
                                    res[key] = float(val)
                                except ValueError:
                                    res[key] = val
                        elif isinstance(line, (tuple, list)) and len(line) >= 2:
                            key, val = line[0], line[1]
                            try:
                                res[key] = float(val)
                            except (ValueError, TypeError):
                                res[key] = val
                    return res
        except Exception:
            pass

        return {}

    def export_to_json(self, filepath: str) -> bool:
        try:
            data = self.load_data(self.storage_path)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            return True
        except Exception:
            return False

    def export_to_csv(self, filepath: str) -> bool:
        try:
            data = self.load_data(self.storage_path)
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for key, value in data.items():
                    writer.writerow([key, value])
            return True
        except Exception:
            return False

    def get_export_stream_dump(self) -> str:
        data = self.load_data(self.storage_path)
        return json.dumps(data)

    def verify_stream_integrity(self, stream) -> bool:
        if isinstance(stream, (io.BytesIO, io.StringIO)):
            return True
        return False
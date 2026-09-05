import os
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. СЕРВЕР ЖИЗНИ ДЛЯ RENDER (БЕЗ НЕГО КОНТЕЙНЕР УМРЕТ)
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Unga-Bunga is breathing!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. ПРОВЕРКА ЩУПАЛЕЦ (GITHUB API)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()

def check_github_connection():
    print("\n==========================================")
    print("   УНГА-БУНГА: ПРОВЕРКА РЕФЛЕКСОВ          ")
    print("==========================================")
    
    if not GITHUB_TOKEN or not GITHUB_REPO:
        print("[!] ОШИБКА: GITHUB_TOKEN или GITHUB_REPO не найдены в переменных Render!")
        return False
        
    url = f"https://api.github.com/repos/{GITHUB_REPO}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            repo_name = data.get("full_name")
            is_private = data.get("private")
            default_branch = data.get("default_branch")
            print(f"[+] СВЯЗЬ С GITHUB УСПЕШНА!")
            print(f"[*] Репозиторий: {repo_name} (Приватный: {is_private})")
            print(f"[*] Основная ветка: {default_branch}")
            return True
        elif r.status_code == 401:
            print("[-] ОШИБКА АВТОРИЗАЦИИ (401): Неверный GITHUB_TOKEN.")
        elif r.status_code == 404:
            print("[-] ОШИБКА (404): Репозиторий не найден. Проверь имя в GITHUB_REPO.")
        else:
            print(f"[-] СБОЙ GITHUB API: Код {r.status_code} | {r.text}")
    except Exception as e:
        print(f"[!] СЕТЕВОЙ СБОЙ ПРИ ЗАПРОСЕ К GITHUB: {e}")
        
    return False

if __name__ == "__main__":
    check_github_connection()
    print("\n[*] Система в режиме ожидания команд...\n")
    # Блокируем завершение главного потока, чтобы процесс жил
    threading.Event().wait()

import os
import requests
import threading
import base64
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. СЕРВЕР ЖИЗНИ ДЛЯ RENDER
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

# 2. РАБОТА С GITHUB API
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_main_sha():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/git/ref/heads/main"
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()["object"]["sha"]
    return None

def create_branch(branch_name, source_sha):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/git/refs"
    payload = {
        "ref": f"refs/heads/{branch_name}",
        "sha": source_sha
    }
    r = requests.post(url, headers=API_HEADERS, json=payload, timeout=10)
    if r.status_code == 201:
        print(f"[+] Ветка '{branch_name}' успешно создана.")
        return True
    elif r.status_code == 422:
        print(f"[*] Ветка '{branch_name}' уже существует, работаем в ней.")
        return True
    else:
        print(f"[-] Ошибка создания ветки: {r.status_code} | {r.text}")
        return False

def push_test_file(branch_name, file_path, content_str):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
    
    # GitHub требует контент строго в base64
    encoded_content = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")
    
    # Проверяем, существует ли уже файл (чтобы забрать его sha при обновлении)
    sha = None
    check_r = requests.get(f"{url}?ref={branch_name}", headers=API_HEADERS, timeout=10)
    if check_r.status_code == 200:
        sha = check_r.json().get("sha")

    payload = {
        "message": "Унга-бунга оставил след на скале (тест записи)",
        "content": encoded_content,
        "branch": branch_name
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(url, headers=API_HEADERS, json=payload, timeout=10)
    if r.status_code in [200, 201]:
        print(f"[+] Файл '{file_path}' успешно запушен в ветку '{branch_name}'!")
        return True
    else:
        print(f"[-] Ошибка записи файла: {r.status_code} | {r.text}")
        return False

def test_motor_skills():
    print("\n==========================================")
    print("   УНГА-БУНГА: ТЕСТ МОТОРИКИ (ЗАПИСЬ)    ")
    print("==========================================")
    
    main_sha = get_main_sha()
    if not main_sha:
        print("[-] Не удалось получить SHA ветки main.")
        return
        
    print(f"[*] Базовый коммит main: {main_sha[:7]}")
    
    test_branch = "unga-mutation-test"
    if create_branch(test_branch, main_sha):
        push_test_file(test_branch, "dna.txt", "Унга-бунга сделал первую палку-копалку.")

if __name__ == "__main__":
    test_motor_skills()
    print("\n[*] Ожидание дальнейших инструкций...\n")
    threading.Event().wait()

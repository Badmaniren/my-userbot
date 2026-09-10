import os
import time
import base64
import re
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. СЕРВЕР ЖИЗНИ ДЛЯ RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Unga is mutating!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. КОНФИГУРАЦИЯ
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_file_content(branch: str, path: str):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}?ref={branch}"
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        encoded = r.json().get("content", "")
        return base64.b64decode(encoded).decode("utf-8")
    return None

def ask_gemini_mutation(original_code: str) -> str:
    if not API_KEYS:
        print("[-] Нет ключей GEMINI_API_KEY!")
        return ""
    
    key = API_KEYS[0]
    # Используем стабильную быструю модель
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    
    prompt = (
        "Ты — автономный мутатор кода. Вот файл victim.py:\n\n"
        f"{original_code}\n\n"
        "ЗАДАЧА: Перепиши функцию solve_task(a, b) так, чтобы она могла принимать как int/float, "
        "так и строки с числами (например, '5' и '10' -> 15). "
        "Базовые тесты (где передаются int) ОБЯЗАНЫ проходить успешно. "
        "ТРЕБОВАНИЕ: Верни ТОЛЬКО чистый код Python без кавычек markdown (без ```python), без комментариев и объяснений."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
    if r.status_code == 200:
        ans = r.json()['candidates'][0]['content']['parts'][0]['text']
        # Вычищаем markdown, если модель все-таки намусорила
        clean_code = re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
        return clean_code
    else:
        print(f"[-] Сбой Gemini API: {r.status_code} | {r.text}")
        return ""

def push_mutation(branch: str, path: str, new_code: str):
    # Получаем SHA main
    ref_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/git/ref/heads/main"
    main_sha = requests.get(ref_url, headers=API_HEADERS, timeout=10).json()["object"]["sha"]
    
    # Создаем или пересоздаем ветку
    branch_ref_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/git/refs/heads/{branch}"
    del_r = requests.delete(branch_ref_url, headers=API_HEADERS, timeout=10) # удаляем старую попытку если была
    time.sleep(1)
    
    create_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/git/refs"
    requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": main_sha}, timeout=10)

    # Пушим файл
    file_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/contents/{path}"
    encoded = base64.b64encode(new_code.encode("utf-8")).decode("utf-8")
    
    payload = {
        "message": "Эволюционная мутация: адаптация типов solve_task",
        "content": encoded,
        "branch": branch
    }
    r = requests.put(file_url, headers=API_HEADERS, json=payload, timeout=10)
    return r.status_code in [200, 201]

def watch_arena(branch: str):
    print(f"[*] Ждем запуска Арены GitHub Actions для ветки '{branch}'...")
    time.sleep(10)
    
    runs_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/actions/runs?branch={branch}"
    for _ in range(12): # Ждем максимум минуту
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                status = latest.get("status")
                conclusion = latest.get("conclusion")
                
                print(f"[~] Статус теста: {status} | Результат: {conclusion}")
                if status == "completed":
                    if conclusion == "success":
                        print("\n==========================================")
                        print("  [+] ЭВОЛЮЦИЯ УСПЕШНА! ТЕСТЫ ПРОЙДЕНЫ!   ")
                        print("==========================================\n")
                    else:
                        print("\n==========================================")
                        print("  [-] ПРИМАТ ПОГИБ: ТЕСТЫ ПРОВАЛЕНЫ!      ")
                        print("==========================================\n")
                    return
        time.sleep(5)
    print("[-] Таймаут ожидания результатов тестов.")

def run_evolution():
    print("\n[!] ЗАПУСК ЦИКЛА МУТАЦИИ...")
    original = get_file_content("main", "victim.py")
    if not original:
        print("[-] Не найден victim.py в ветке main!")
        return
        
    print(f"[*] Текущий код:\n{original}\n")
    mutated = ask_gemini_mutation(original)
    if not mutated:
        print("[-] Мутация сорвалась.")
        return
        
    print(f"[*] Код от Gemini:\n{mutated}\n")
    branch = "unga-mutation-v1"
    if push_mutation(branch, "victim.py", mutated):
        print(f"[+] Мутация залита в ветку '{branch}'!")
        watch_arena(branch)

if __name__ == "__main__":
    run_evolution()
    threading.Event().wait()

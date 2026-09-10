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
        self.wfile.write(b"Unga is alive and mutating!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. СБОРКА АДРЕСОВ БЕЗ УРОДОВАНИЯ МОБИЛЬНЫМ БУФЕРОМ
def clean_url(url: str) -> str:
    url = re.sub(r'\[.*?\]\(\vert{}\)', '', url)
    return url.strip()

API_HOST = "generativelanguage.googleapis.com"
API_BASE = "https://" + API_HOST + "/v1beta/"

GITHUB_HOST = "api.github.com"
GITHUB_BASE = "https://" + GITHUB_HOST + "/repos/"

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]
KEY_INDEX = 0

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_current_key():
    global KEY_INDEX
    if not API_KEYS:
        return ""
    return API_KEYS[KEY_INDEX % len(API_KEYS)]

def rotate_key():
    global KEY_INDEX
    if len(API_KEYS) > 1:
        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        print(f"[!] СМЕНА КЛЮЧА GEMINI. Новый индекс: {KEY_INDEX}")

def get_viable_models(key: str) -> list:
    url = clean_url(f"{API_BASE}models?key={key}")
    viable = []
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = r.json().get("models", [])
            available = [m["name"] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
            flash_models = [m for m in available if "flash" in m.lower() and "preview" not in m.lower()]
            other_models = [m for m in available if m not in flash_models]
            
            candidates = flash_models + other_models
            print(f"[*] Прощупываем кандидатов (лимит: 3)...")
            for m in candidates:
                test_url = clean_url(f"{API_BASE}{m}:generateContent?key={key}")
                try:
                    res = requests.post(test_url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=8)
                    if res.status_code == 200:
                        print(f"[+] Подтверждена живая модель: {m}")
                        viable.append(m)
                        if len(viable) >= 3:
                            break
                except Exception:
                    continue
    except Exception as e:
        print(f"[-] Ошибка опроса моделей: {e}")
    return viable

def get_file_content(branch: str, path: str):
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        encoded = r.json().get("content", "")
        return base64.b64decode(encoded).decode("utf-8")
    return None

def ask_gemini_mutation(original_code: str) -> str:
    if not API_KEYS:
        print("[-] Ошибка: список GEMINI_API_KEY пуст.")
        return ""

    prompt = (
        "Ты — мутатор кода. Вот файл victim.py:\n\n"
        f"{original_code}\n\n"
        "ЗАДАЧА: Перепиши функцию solve_task(a, b) так, чтобы она могла принимать как int/float, "
        "так и строки с числами (например, '5' и '10' -> 15). "
        "Базовые тесты (где передаются int) ОБЯЗАНЫ проходить успешно. "
        "ТРЕБОВАНИЕ: Верни ТОЛЬКО валидный код Python без markdown (без ```python), без комментариев."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }

    for attempt in range(5):
        current_key = get_current_key()
        models_pool = get_viable_models(current_key)
        
        if not models_pool:
            print("[-] Нет живых моделей на ключе. Ротируем ключ...")
            rotate_key()
            time.sleep(2)
            continue

        for model_name in models_pool:
            url = clean_url(f"{API_BASE}{model_name}:generateContent?key={current_key}")
            print(f"[~] Генерация через {model_name} (ключ #{KEY_INDEX})...")
            
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
                if r.status_code == 200:
                    ans = r.json()['candidates'][0]['content']['parts'][0]['text']
                    clean_code = re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
                    return clean_code
                
                print(f"[-] Сбой {model_name}: код {r.status_code}")
                if r.status_code in [429, 503]:
                    rotate_key()
                    current_key = get_current_key()
                    time.sleep(3)
            except Exception as e:
                print(f"[-] Ошибка сети Gemini: {e}")
                time.sleep(2)
                
    return ""

def push_mutation(branch: str, path: str, new_code: str):
    ref_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    ref_res = requests.get(ref_url, headers=API_HEADERS, timeout=10)
    if ref_res.status_code != 200:
        print(f"[-] Ошибка получения SHA ветки main: {ref_res.status_code} | {ref_res.text}")
        return False
        
    main_sha = ref_res.json()["object"]["sha"]
    
    branch_ref_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    requests.delete(branch_ref_url, headers=API_HEADERS, timeout=10)
    time.sleep(1)
    
    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    create_res = requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": main_sha}, timeout=10)
    if create_res.status_code not in [201, 422]:
        print(f"[-] Ошибка создания ветки: {create_res.status_code}")
        return False

    file_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}")
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
    time.sleep(8)
    
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs?branch={branch}")
    for _ in range(12):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                status = latest.get("status")
                conclusion = latest.get("conclusion")
                
                print(f"[~] Арена: статус {status} | вердикт: {conclusion}")
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
    print("[-] Таймаут ожидания тестов.")

def run_evolution():
    print("\n[!] ЗАПУСК ЦИКЛА МУТАЦИИ...")
    original = get_file_content("main", "victim.py")
    if not original:
        print("[-] Не найден victim.py в ветке main!")
        return
        
    print(f"[*] Исходник:\n{original}\n")
    mutated = ask_gemini_mutation(original)
    if not mutated:
        print("[-] Мутация сорвалась.")
        return
        
    print(f"[*] Сгенерированный код:\n{mutated}\n")
    branch = "unga-mutation-v1"
    if push_mutation(branch, "victim.py", mutated):
        print(f"[+] Мутация запушена в ветку '{branch}'!")
        watch_arena(branch)
    else:
        print("[-] Не удалось запушить мутацию на GitHub.")

if __name__ == "__main__":
    try:
        run_evolution()
    except Exception as e:
        print(f"\n[!!!] КРИТИЧЕСКИЙ СБОЙ В ЦИКЛЕ: {e}")
        print("[*] Аварийный перехват сработал: сервис остается жить, рестарта не будет.\n")
        
    print("[*] Переход в фоновый режим ожидания...")
    threading.Event().wait()

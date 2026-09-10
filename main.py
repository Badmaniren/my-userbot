import os
import time
import base64
import re
import json
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. ЖИВУЧИЙ ВЕБ-СЕРВЕР ДЛЯ RENDER
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pithecanthropus Triad is operational.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. ИНФРАСТРУКТУРА И СЕТЬ
def clean_url(url: str) -> str:
    return re.sub(r'\[.*?\]\(|\)', '', url).strip()

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
    return API_KEYS[KEY_INDEX % len(API_KEYS)] if API_KEYS else ""

def rotate_key():
    global KEY_INDEX
    if len(API_KEYS) > 1:
        KEY_INDEX = (KEY_INDEX + 1) % len(API_KEYS)
        print(f"[!] Ротация ключа Gemini -> индекс #{KEY_INDEX}")

def get_viable_models(key: str) -> list:
    url = clean_url(f"{API_BASE}models?key={key}")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            models = r.json().get("models", [])
            available = [m["name"] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
            flash_models = [m for m in available if "flash" in m.lower() and "preview" not in m.lower()]
            candidates = flash_models + [m for m in available if m not in flash_models]
            viable = []
            for m in candidates:
                test_url = clean_url(f"{API_BASE}{m}:generateContent?key={key}")
                try:
                    res = requests.post(test_url, json={"contents": [{"parts": [{"text": "hi"}]}]}, timeout=8)
                    if res.status_code == 200:
                        viable.append(m)
                        if len(viable) >= 2:
                            break
                except Exception:
                    continue
            return viable
    except Exception:
        pass
    return []

def ask_gemini(prompt: str, json_mode: bool = False) -> str:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json" if json_mode else "text/plain"
        }
    }
    for _ in range(4):
        key = get_current_key()
        models = get_viable_models(key)
        if not models:
            rotate_key()
            time.sleep(2)
            continue
        for model in models:
            url = clean_url(f"{API_BASE}{model}:generateContent?key={key}")
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
                if r.status_code == 200:
                    ans = r.json()['candidates'][0]['content']['parts'][0]['text']
                    if not json_mode:
                        return re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
                    return ans.strip()
                if r.status_code in [429, 503]:
                    rotate_key()
                    time.sleep(2)
            except Exception:
                time.sleep(2)
    return ""

def get_existing_skills() -> list:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/skills?ref=main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    if r.status_code == 200:
        return [f["name"] for f in r.json() if f["name"].endswith(".py") and f["name"] != "__init__.py"]
    return []

def get_main_sha() -> str:
    url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/ref/heads/main")
    r = requests.get(url, headers=API_HEADERS, timeout=10)
    return r.json()["object"]["sha"] if r.status_code == 200 else ""

def prepare_branch(branch: str, base_sha: str):
    del_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}")
    requests.delete(del_url, headers=API_HEADERS, timeout=10)
    time.sleep(1)
    create_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs")
    requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": base_sha}, timeout=10)

def commit_file_to_branch(branch: str, path: str, content: str, msg: str):
    file_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}?ref={branch}")
    f_info = requests.get(file_url, headers=API_HEADERS, timeout=10)
    sha = f_info.json().get("sha") if f_info.status_code == 200 else None

    payload = {
        "message": msg,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
    requests.put(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/contents/{path}"), headers=API_HEADERS, json=payload, timeout=10)

def watch_arena(branch: str, exclude_id=None):
    time.sleep(8)
    runs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs?branch={branch}")
    for _ in range(16):
        r = requests.get(runs_url, headers=API_HEADERS, timeout=10)
        if r.status_code == 200:
            runs = r.json().get("workflow_runs", [])
            if runs:
                latest = runs[0]
                run_id = latest.get("id")
                if exclude_id and run_id == exclude_id:
                    time.sleep(4)
                    continue
                if latest.get("status") == "completed":
                    return latest.get("conclusion") == "success", run_id
        time.sleep(5)
    return False, None

# ТОЧНОЕ ИЗВЛЕЧЕНИЕ ОШИБОК ИЗ ТЕСТОВ (БЕЗ МУСОРА РАННЕРА)
def extract_clean_test_traceback(run_id: int) -> str:
    jobs_url = clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/runs/{run_id}/jobs")
    r = requests.get(jobs_url, headers=API_HEADERS, timeout=10)
    if r.status_code != 200:
        return "Не удалось связаться с API логов."
    jobs = r.json().get("jobs", [])
    failed = next((j for j in jobs if j.get("conclusion") == "failure"), None)
    if not failed:
        return "Сбойных шагов не найдено."
    
    log_res = requests.get(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/actions/jobs/{failed['id']}/logs"), headers=API_HEADERS, timeout=15)
    if log_res.status_code != 200:
        return "Тело логов недоступно."

    lines = log_res.text.splitlines()
    error_buffer = []
    capture = False

    for line in lines:
        cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s*', '', line).strip()
        # Старт захвата при падении юнит-тестов
        if any(marker in cleaned for marker in ["FAIL:", "ERROR:", "Traceback (most recent call last):"]):
            capture = True
        if capture:
            # Игнорируем технические команды runner'а
            if not cleaned.startswith("[command]") and "node-20" not in cleaned.lower():
                error_buffer.append(cleaned)
        if capture and cleaned.startswith("FAILED ("):
            break

    if error_buffer:
        return "\n".join(error_buffer[-35:])
    return "Тесты упали, но точный traceback не распознан."

# 3. ТРИАДА
def dream_new_skill(existing_skills: list) -> dict:
    prompt = (
        "Ты — Фантазер. Директива: ТЕХНО-ПАРАЗИТИЗМ. Среда: бесплатный инстанс Render (512MB RAM).\n"
        f"УЖЕ ИМЕЮЩИЕСЯ НАВЫКИ В skills/: {existing_skills}\n\n"
        "ЗАДАЧА: Придумай ОДИН новый полезный инструмент Python. "
        "Ты МОЖЕШЬ придумать самостоятельную утилиту или СИНЕРГЕТИЧЕСКИЙ модуль, "
        "который импортирует и комбинирует уже существующие навыки (например, связка http_ping + file_cache + clean_text "
        "для создания парсера RSS-лент или безопасного сборщика публичных API).\n"
        "ТРЕБОВАНИЯ: Только стандартная библиотека Python или requests. Никаких платных сервисов.\n"
        "Верни СТРОГО валидный JSON:\n"
        "{\n"
        '  "module_name": "имя_модуля_без_py",\n'
        '  "description": "описание назначения",\n'
        '  "class_or_func": "сигнатура основных функций или классов"\n'
        "}"
    )
    raw = ask_gemini(prompt, json_mode=True)
    try:
        return json.loads(raw)
    except Exception:
        fallback_name = f"rss_feed_{int(time.time())}"
        return {
            "module_name": fallback_name,
            "description": "Парсер XML/RSS лент с извлечением заголовков и ссылок",
            "class_or_func": "parse_feed(xml_data: str) -> list"
        }

def architect_write_tests(skill_info: dict) -> str:
    prompt = (
        "Ты — Архитектор. Напиши юнит-тесты unittest для модуля:\n"
        f"{json.dumps(skill_info, ensure_ascii=False)}\n\n"
        f"Путь импорта: `from skills.{skill_info['module_name']} import ...`\n\n"
        "ТРЕБОВАНИЯ:\n"
        "1. Использовать `unittest`.\n"
        "2. Тесты обязаны быть АВТОНОМНЫМИ — никаких реальных запросов в сеть! "
        "Тестируй логику обработки сырых строк, mock-ответов или структур данных.\n"
        "3. Напиши 4-5 жестких сценариев, проверяющих краевые случаи.\n"
        "4. Верни ТОЛЬКО валидный Python-код без markdown."
    )
    return ask_gemini(prompt)

def unga_write_implementation(skill_info: dict, test_code: str, error_log: str = "") -> str:
    context = f"ОШИБКА АРЕНЫ С ПРОШЛОГО ПРОГОНА:\n{error_log}\n" if error_log else "Первичная разработка."
    prompt = (
        "Ты — Унга-кодер. Реализуй модуль Python, который пройдет тесты Архитектора.\n"
        f"Имя файла: skills/{skill_info['module_name']}.py\n"
        f"Описание: {skill_info['description']}\n\n"
        f"ТЕСТЫ (ОБЯЗАН ИХ ПРОЙТИ):\n{test_code}\n\n"
        f"{context}\n\n"
        "ТРЕБОВАНИЯ:\n"
        "1. Полная реализация без заглушек 'pass'.\n"
        "2. Используй стандартную библиотеку Python или requests. При необходимости импортируй соседние модули из `skills.`\n"
        "3. Верни ТОЛЬКО чистый код Python без markdown."
    )
    return ask_gemini(prompt)

# 4. ЦИКЛ И КУЛДАУН
def run_triad_iteration():
    print("\n==========================================")
    print("      ПИТЕКАНТРОП: ИТЕРАЦИЯ ЭВОЛЮЦИИ      ")
    print("==========================================")
    
    existing = get_existing_skills()
    print(f"[*] Освоенные навыки: {existing}")

    print("\n[1/4] ФАНТАЗЕР: Поиск новой формы...")
    idea = dream_new_skill(existing)
    mod_name = re.sub(r'[^a-zA-Z0-9_]', '', idea.get("module_name", "tool").lower())
    print(f"[+] Задуман модуль: '{mod_name}'")
    print(f"[*] Суть: {idea.get('description')}")

    print("\n[2/4] АРХИТЕКТОР: Сборка контракта...")
    test_code = architect_write_tests(idea)
    
    branch = f"unga-skill-{mod_name}"
    prepare_branch(branch, get_main_sha())
    
    test_path = f"test_{mod_name}.py"
    skill_path = f"skills/{mod_name}.py"
    
    commit_file_to_branch(branch, "skills/__init__.py", "# unga skills\n", "Init package")
    commit_file_to_branch(branch, test_path, test_code, f"Тесты для {mod_name}")

    print("\n[3/4] УНГА: Первичная реализация...")
    impl_code = unga_write_implementation(idea, test_code)
    commit_file_to_branch(branch, skill_path, impl_code, f"Реализация {mod_name}")

    print(f"[*] Отправлено на Арену. Ожидание судьи...")
    passed, run_id = watch_arena(branch)
    
    attempts = 1
    while not passed and attempts <= 3:
        print(f"\n[!] САМОИСЦЕЛЕНИЕ: Раунд #{attempts} для '{mod_name}'")
        err = extract_clean_test_traceback(run_id)
        print(f"[!] ЧИСТЫЙ ТРЕЙСБЕК:\n{err}\n")
        
        impl_code = unga_write_implementation(idea, test_code, error_log=err)
        commit_file_to_branch(branch, skill_path, impl_code, f"Исцеление #{attempts}")
        passed, run_id = watch_arena(branch, exclude_id=run_id)
        attempts += 1

    if passed:
        print(f"\n[+] НАВЫК '{mod_name}' ВЫЖИЛ И ДОКАЗАЛ СИЛУ!")
        requests.post(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/merges"), headers=API_HEADERS, json={
            "base": "main", "head": branch, "commit_message": f"ЭВОЛЮЦИЯ: Вливание skills/{mod_name}.py"
        }, timeout=10)
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)
        print(f"[+] Модуль ассимилирован в main.")
    else:
        print(f"\n[-] Мутация '{mod_name}' нежизнеспособна и уничтожена.")
        requests.delete(clean_url(f"{GITHUB_BASE}{GITHUB_REPO}/git/refs/heads/{branch}"), headers=API_HEADERS)

def life_cycle():
    while True:
        try:
            run_triad_iteration()
        except Exception as e:
            print(f"[!] Ошибка итерации: {e}")
            
        print("\n[*] Метаболизм замедлен: сон 20 минут перед следующей мутацией...\n")
        time.sleep(1200)

if __name__ == "__main__":
    threading.Thread(target=life_cycle, daemon=True).start()
    threading.Event().wait()

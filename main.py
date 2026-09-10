import os
import time
import base64
import re
import requests
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. СЕРВЕР ЖИЗНИ ДЛЯ RENDER (С ПОДДЕРЖКОЙ HEAD И GET)
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

# 2. КОНФИГУРАЦИЯ
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.environ.get("GITHUB_REPO", "").strip()
RAW_KEYS = os.environ.get("GEMINI_API_KEY", "").strip()
API_KEYS = [k.strip() for k in RAW_KEYS.split(",") if k.strip()]

API_HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# ЖЕСТКИЙ ПРОЗВОН МОДЕЛЕЙ БОЕВЫМ МИКРО-ЗАПРОСОМ
def find_working_gemini_model(key: str) -> str:
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    try:
        r = requests.get(list_url, timeout=10)
        if r.status_code != 200:
            print(f"[-] Ошибка получения списка моделей: {r.status_code}")
            return ""
        
        models = r.json().get("models", [])
        available = [m["name"] for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
        
        # Сортируем: сначала свежие flash, потом остальные
        flash_models = [m for m in available if "flash" in m.lower() and "preview" not in m.lower()]
        candidates = flash_models + [m for m in available if m not in flash_models]

        print(f"[*] Прощупываем кандидатов на боевом запросе (всего: {len(candidates)})...")
        for model_name in candidates:
            test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": "ping"}]}]}
            
            test_res = requests.post(test_url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            if test_res.status_code == 200:
                print(f"[+] НАЙДЕНА РЕАЛЬНО РАБОЧАЯ МОДЕЛЬ: {model_name}")
                return model_name
            else:
                print(f"[-] {model_name} отклонена (код {test_res.status_code})")
                
    except Exception as e:
        print(f"[-] Сбой при поиске модели: {e}")
    return ""

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
    model_name = find_working_gemini_model(key)
    if not model_name:
        print("[-] Не найдено ни одной живой модели для генерации.")
        return ""

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={key}"
    
    prompt = (
        "Ты — мутатор кода. Вот файл victim.py:\n\n"
        f"{original_code}\n\n"
        "ЗАДАЧА: Перепиши функцию solve_task(a, b) так, чтобы она могла принимать как int/float, "
        "так и строки с числами (например, '5' и '10' -> 15). "
        "Базовые тесты (где передаются int) ОБЯЗАНЫ проходить успешно. "
        "ТРЕБОВАНИЕ: Верни ТОЛЬКО валидный код Python без markdown (без ```python), без пояснений."
    )
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2}
    }
    
    r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=25)
    if r.status_code == 200:
        ans = r.json()['candidates'][0]['content']['parts'][0]['text']
        clean_code = re.sub(r'```[a-zA-Z]*', '', ans).replace('```', '').strip()
        return clean_code
    else:
        print(f"[-] Сбой генерации: {r.status_code} | {r.text}")
        return ""

def push_mutation(branch: str, path: str, new_code: str):
    ref_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/git/ref/heads/main"
    main_sha = requests.get(ref_url, headers=API_HEADERS, timeout=10).json()["object"]["sha"]
    
    branch_ref_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/git/refs/heads/{branch}"
    requests.delete(branch_ref_url, headers=API_HEADERS, timeout=10)
    time.sleep(1)
    
    create_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/git/refs"
    requests.post(create_url, headers=API_HEADERS, json={"ref": f"refs/heads/{branch}", "sha": main_sha}, timeout=10)

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
    print(f"[*] Ждем вердикта Арены GitHub Actions для '{branch}'...")
    time.sleep(8)
    
    runs_url = f"[https://api.github.com/repos/](https://api.github.com/repos/){GITHUB_REPO}/actions/runs?branch={branch}"
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
                        print("  [+] ЭВОЛЮЦИЯ УСПЕШНА! ТЕСТЫ ВЫДЕРЖАНЫ! ")
                        print("==========================================\n")
                    else:
                        print("\n==========================================")
                        print("  [-] МУТАЦИЯ ПРОВАЛИЛАСЬ: КОД КАЗНЕН!   ")
                        print("==========================================\n")
                    return
        time.sleep(5)
    print("[-] Таймаут ожидания тестов.")

def run_evolution():
    print("\n[!] ЗАПУСК ЦИКЛА ЭВОЛЮЦИИ...")
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
        print(f"[+] Мутация запушена в '{branch}'!")
        watch_arena(branch)

if __name__ == "__main__":
    run_evolution()
    threading.Event().wait()

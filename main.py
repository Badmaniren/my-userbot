import os
import requests
import asyncio
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pyrogram import Client, filters

# Микро-вебсервер для обмана Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Userbot is alive!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# Настройки и ключи
API_ID = int(os.environ.get("API_ID", "31001164"))
API_HASH = os.environ.get("API_HASH", "18ae94f76873c93be328527e858de657")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

WORKING_MODEL = None

def find_working_model():
    list_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    try:
        res = requests.get(list_url).json()
        if 'models' not in res: return None
        for m in res['models']:
            model_name = m['name']
            if 'generateContent' in m.get('supportedGenerationMethods', []):
                test_url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GEMINI_API_KEY}"
                payload = {"contents": [{"parts": [{"text": "hi"}]}]}
                r = requests.post(test_url, json=payload, headers={'Content-Type': 'application/json'})
                if r.status_code == 200:
                    return model_name
    except Exception:
        pass
    return None

def ask_gemini(user_text):
    global WORKING_MODEL
    if not WORKING_MODEL:
        WORKING_MODEL = find_working_model()
    if not WORKING_MODEL:
        return "Я сейчас немного туплю, отвечу позже."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {
            "parts": [{
                "text": "Ты — живой пацан в личке Telegram. Отвечай СТРОГО на русском языке, коротко (1-2 предложения), без формальностей. КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО писать на английском, выдавать свои мысли, разборы или слова вроде 'Wait', 'Option', 'Instruction'."
            }]
        },
        "contents": [{
            "parts": [{"text": f"Собеседник пишет тебе: {user_text}"}]
        }]
    }
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'candidates' in response and len(response['candidates']) > 0:
            raw_answer = response['candidates'][0]['content']['parts'][0]['text']
            lines = [l.strip() for l in raw_answer.split('\n') if l.strip()]
            clean_lines = []
            for line in lines:
                if line.startswith('*') or line.startswith('-'):
                    continue
                if any(w in line.lower() for w in ['wait', 'instruction', 'responding', 'constraint', 'option', 'should just']):
                    continue
                clean_lines.append(line)
            if clean_lines:
                ans = clean_lines[-1]
                if ans.startswith('"') and ans.endswith('"'):
                    ans = ans[1:-1]
                return ans
            return "Здарова! Чё как?"
    except Exception as e:
        print(f"Ошибка: {e}")
    return "Давай потом перетрем, занят."

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    print(f"\n[!] Личка от {sender_name}: {message.text}")
    delay = random.randint(3, 6)
    await asyncio.sleep(delay)
    reply_text = ask_gemini(message.text)
    await message.reply(reply_text)
    print(f"[+] Отвечено: {reply_text}")

print("Юзербот стартовал на Render Web Service!")

# Фикс цикла событий для новых версий Python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

app.run()

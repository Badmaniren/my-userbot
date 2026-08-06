import os
import requests
import asyncio
import random
import threading
import re
from http.server import HTTPServer, BaseHTTPRequestHandler

# Костыль для новых версий Python
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

from pyrogram import Client, filters, idle

# Микро-вебсервер
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

# Ключи
API_ID = int(os.environ.get("API_ID", "31001164"))
API_HASH = os.environ.get("API_HASH", "18ae94f76873c93be328527e858de657")
SESSION_STRING = os.environ.get("SESSION_STRING")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

app = Client("my_account", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING)

WORKING_MODEL = None
HISTORY = {}

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

def ask_gemini(user_id, user_text):
    global WORKING_MODEL, HISTORY
    if not WORKING_MODEL:
        WORKING_MODEL = find_working_model()
    if not WORKING_MODEL:
        return "Я сейчас немного туплю, отвечу позже."
    
    if user_id not in HISTORY:
        HISTORY[user_id] = []
        
    HISTORY[user_id].append({"sender": "Собеседник", "text": user_text})
    
    if len(HISTORY[user_id]) > 8:
        HISTORY[user_id] = HISTORY[user_id][-8:]
        
    dialogue = "\n".join([f"{msg['sender']}: {msg['text']}" for msg in HISTORY[user_id]])
    
    prompt = f"История переписки:\n{dialogue}\n\nНапиши СВОЮ реплику."

    url = f"https://generativelanguage.googleapis.com/v1beta/{WORKING_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "systemInstruction": {
            "parts": [{
                "text": "Ты дерзкий пацан. ВЫДАЙ ТОЛЬКО ОДНУ ФРАЗУ НА РУССКОМ. КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ писать списки, рассуждения, мета-теги или использовать английский язык. ТОЛЬКО ГОЛЫЙ ТЕКСТ ОТВЕТА."
            }]
        },
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'}).json()
        if 'candidates' in response and len(response['candidates']) > 0:
            raw_answer = response['candidates'][0]['content']['parts'][0]['text']
            
            # ЖЕСТКАЯ МЯСОРУБКА: Парсим ответ и убиваем мысли вслух
            lines = [l.strip() for l in raw_answer.split('\n') if l.strip()]
            clean_lines = []
            
            for line in lines:
                # Убиваем строки со списками и английскими словами-паразитами
                lower_line = line.lower()
                if line.startswith('*') or line.startswith('-'):
                    continue
                if any(word in lower_line for word in ['option', 'decision', 'actually', 'let\'s', 'wait', 'instruction', 'persona', 'style', 'text:', 'response:', 'selected:', 'reply:']):
                    continue
                clean_lines.append(line)
            
            # Достаем последнюю выжившую строку
            if clean_lines:
                ans = clean_lines[-1]
                # Срезаем кавычки по краям, если этот дебил их оставил
                ans = re.sub(r'^"|"$', '', ans).strip()
                ans = re.sub(r'^(\*.*?\*|\[.*?\])', '', ans).strip()
                
                HISTORY[user_id].append({"sender": "Ты", "text": ans})
                return ans
            else:
                # Если он вывел ТОЛЬКО английский мусор
                HISTORY[user_id].pop()
                return "Давай потом, я че-то завис."
                
    except Exception as e:
        print(f"Ошибка: {e}")
        
    HISTORY[user_id].pop()
    return "Давай потом перетрем, занят."

@app.on_message(filters.private & ~filters.me & ~filters.bot)
async def auto_reply(client, message):
    sender_name = message.from_user.first_name if message.from_user else "Кто-то"
    user_id = message.from_user.id
    
    print(f"\n[!] Личка от {sender_name}: {message.text}")
    delay = random.randint(3, 6)
    await asyncio.sleep(delay)
    
    reply_text = ask_gemini(user_id, message.text)
    
    await message.reply(reply_text)
    print(f"[+] Отвечено: {reply_text}")

async def main():
    await app.start()
    print("\n==========================================")
    print(" ЮЗЕРБОТ СТАРТОВАЛ (ПОСЛЕ ЛОБОТОМИИ) ")
    print("==========================================\n")
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop.run_until_complete(main())

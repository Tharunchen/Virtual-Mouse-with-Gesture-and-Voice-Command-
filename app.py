import eel
import os
import subprocess
import datetime
import re
import screen_brightness_control as sbc
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import threading
import time
import keyboard
from googletrans import Translator
from gtts import gTTS
import tempfile
import pygame
import psutil
import requests
import pyjokes

# -------------------- Volume Setup --------------------
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))

eel.init("web")

VOLUME_STEP = 0.1
BRIGHTNESS_STEP = 10
CHROME_PATH = r"C:/Program Files/Google/Chrome/Application/chrome.exe"

mic_active = False
translator = Translator()

# Default language
selected_lang = "en"

# API Keys (replace with your own for live data)
OPENWEATHER_KEY = "http://api.weatherapi.com/v1/current.json?key=&q=London"
NEWSAPI_KEY = "YOUR_NEWSAPI_API_KEY"

# -------------------- Language --------------------
@eel.expose
def setLanguage(lang_code):
    global selected_lang
    selected_lang = lang_code



def ai_chat(prompt):
    try:
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        headers = {"Authorization": "Bearer YOUR_HF_API_KEY"}
        payload = {"inputs": prompt}
        response = requests.post(url, headers=headers, json=payload)
        return response.json()[0]['generated_text']
    except:
        return "Sorry, I can’t chat right now."




# -------------------- Main Chat Logic --------------------
@eel.expose
def getUserInput(msg):
    msg_lower = msg.lower().strip()
    response = ""

    # -------------------- Time / Date / Day --------------------
    if any(word in msg_lower for word in ["time", "date", "day"]):
        parts = []
        if "time" in msg_lower:
            parts.append(f"The current time is {datetime.datetime.now().strftime('%H:%M:%S')}")
        if "date" in msg_lower:
            parts.append(f"Today's date is {datetime.datetime.now().strftime('%Y-%m-%d')}")
        if "day" in msg_lower:
            parts.append(f"Today is {datetime.datetime.now().strftime('%A')}")
        response = ", ".join(parts)

    # -------------------- Exit --------------------
    elif "exit" in msg_lower or "bye" in msg_lower:
        response = "Goodbye Shutting down..."
        sendResponse(response)
        def shutdown():
            time.sleep(1)
            try:
                eel.close_window()
            except:
                pass
            os._exit(0)
        threading.Thread(target=shutdown, daemon=True).start()
        return

    # -------------------- Web Search --------------------
    elif "open and search for" in msg_lower or "search" in msg_lower:
        query = msg_lower.replace("open", "").replace("search", "").replace("for", "").strip()
        if query:
            subprocess.Popen([CHROME_PATH, f"https://www.google.com/search?q={query}"])
            response = f"Searching for {query} in Chrome..."
        else:
            response = "Please say what you want to search for."

    # -------------------- Open Apps --------------------
    elif "open" in msg_lower:
        if "chrome" in msg_lower:
            openApp(CHROME_PATH, "Chrome")
            return
        elif "file explorer" in msg_lower or "explorer" in msg_lower:
            openApp("explorer", "File Explorer")
            return
        elif "notepad" in msg_lower:
            openApp("notepad", "Notepad")
            return
        elif "calculator" in msg_lower:
            openApp("calc", "Calculator")
            return
        elif "word" in msg_lower:
            openApp(r"C:/Program Files/Microsoft Office/root/Office16/WINWORD.EXE", "Microsoft Word")
            return
        elif "vscode" in msg_lower or "vs code" in msg_lower or "visual studio code" in msg_lower:
            subprocess.Popen(["cmd", "/c", "code"])
            response = "Opening VS Code..."
        else:
            response = "Sorry, I don't recognize that app."

    # -------------------- Extra Features --------------------
    elif "weather" in msg_lower:
        response = get_weather("Bangalore")  # default city, can modify
    elif "news" in msg_lower:
        response = get_news()
    elif "joke" in msg_lower:
        response = pyjokes.get_joke()
    elif "status" in msg_lower or "system" in msg_lower:
        response = get_system_status()

    # -------------------- Volume / Brightness --------------------
    else:
        match = re.search(r'(\d+)%?', msg_lower)
        percent_value = int(match.group(1)) if match else None

        if "volume up" in msg_lower or "increase volume" in msg_lower:
            step = percent_value/100 if percent_value else VOLUME_STEP
            current = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(min(1.0, current + step), None)
            response = f" Volume increased"
        elif "volume down" in msg_lower or "decrease volume" in msg_lower:
            step = percent_value/100 if percent_value else VOLUME_STEP
            current = volume.GetMasterVolumeLevelScalar()
            volume.SetMasterVolumeLevelScalar(max(0.0, current - step), None)
            response = f"Volume decreased"
        elif "mute" in msg_lower:
            volume.SetMute(1, None)
            response = "Volume muted"
        elif "brightness up" in msg_lower or "increase brightness" in msg_lower:
            step = percent_value if percent_value else BRIGHTNESS_STEP
            current = sbc.get_brightness()[0]
            sbc.set_brightness(min(100, current + step))
            response = f"Brightness increased"
        elif "brightness down" in msg_lower or "decrease brightness" in msg_lower:
            step = percent_value if percent_value else BRIGHTNESS_STEP
            current = sbc.get_brightness()[0]
            sbc.set_brightness(max(0, current - step))
            response = f"Brightness decreased"
        elif "hello" in msg_lower:
            response = "Hello! How can I help you today?"
                # -------------------- Casual Conversation (Fallback) --------------------
        else:
           # response = ai_chat(msg)   # try casual responses
           # if not response or response.strip() == "":
                response = f"You said: {msg}"   # echo if nothing found


    sendResponse(response)

# -------------------- Send Response --------------------
def sendResponse(text):
    try:
        translated = translator.translate(text, dest=selected_lang).text
        eel.addMsgToChat(translated)

        eel.stopListening()()
        speak_with_gtts(translated, selected_lang)
        eel.startListening()()
    except Exception:
        eel.addMsgToChat(text)

# -------------------- gTTS TTS --------------------
def speak_with_gtts(text, lang):
    try:
        tmp_path = os.path.join(tempfile.gettempdir(), "assistant_tts.mp3")
        tts = gTTS(text=text, lang=lang)
        tts.save(tmp_path)

        pygame.mixer.init()
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.quit()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except Exception as e:
        print(f"TTS error: {e}")

# -------------------- Open App --------------------
def openApp(path_or_cmd, name):
    try:
        if os.path.exists(path_or_cmd):
            os.startfile(path_or_cmd)
        else:
            subprocess.Popen(path_or_cmd)
        msg = f"Opening {name}..."
        sendResponse(msg)
    except Exception:
        msg = f"Failed to open {name}."
        sendResponse(msg)

# -------------------- Extra Feature Functions --------------------
def get_weather(city):
    if not OPENWEATHER_KEY or OPENWEATHER_KEY.startswith("YOUR_"):
        return "Weather not available (no API key)."
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_KEY}&units=metric"
        data = requests.get(url).json()
        if data.get("main"):
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"🌦️ The weather in {city} is {desc} with {temp}°C."
        else:
            return "Couldn't fetch weather right now."
    except:
        return "Weather service unavailable."

def get_news():
    if not NEWSAPI_KEY or NEWSAPI_KEY.startswith("YOUR_"):
        return "News not available (no API key)."
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWSAPI_KEY}"
        data = requests.get(url).json()
        articles = data.get("articles", [])[:3]
        if articles:
            headlines = [f"{i+1}. {a['title']}" for i, a in enumerate(articles)]
            return "Top News:\n" + "\n".join(headlines)
        else:
            return "No news available right now."
    except:
        return "News service unavailable."

def get_system_status():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    if battery:
        return f"💻 CPU: {cpu}% | RAM: {ram}% | Battery: {battery.percent}%"
    else:
        return f"💻 CPU: {cpu}% | RAM: {ram}% | Battery: N/A"

# -------------------- Hotkeys --------------------
def hotkey_listener():
    global mic_active
    keyboard.on_press_key("shift", lambda _: push_to_talk(True))
    keyboard.on_release_key("shift", lambda _: push_to_talk(False))
    while True:
        time.sleep(1)

def push_to_talk(active):
    global mic_active
    if active and not mic_active:
        mic_active = True
        eel.startListening()()
    elif not active and mic_active:
        mic_active = False
        eel.stopListening()()

# -------------------- Main --------------------
if __name__ == "__main__":
    threading.Thread(target=hotkey_listener, daemon=True).start()
    def startup_greeting():
        sendResponse("Hello! I am ready to assist you.")
    threading.Timer(1.0, startup_greeting).start()
    eel.start("index.html", size=(500, 650), block=True)

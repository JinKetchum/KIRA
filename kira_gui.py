import customtkinter as ctk
import threading
import os
import datetime
import webbrowser
import subprocess
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pyautogui
import asyncio
import edge_tts

async def _async_speak(text):
    import asyncio
    await asyncio.sleep(0.3)
    communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
    await communicate.save("E:\\KIRA\\temp_speech.mp3")

# Load env
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

import json

MEMORY_FILE = os.path.join(os.path.expanduser("~"), "Documents", "kira_memory.json")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return [{"role": "system", "content": "You are KIRA (Kinetic Intelligence & Response Assistant), a helpful, smart and friendly AI assistant. Keep responses concise and clear."}]

def save_memory(history):
    with open(MEMORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

conversation_history = load_memory()

KNOWLEDGE_FILE = os.path.join(os.path.expanduser("~"), "Documents", "kira_knowledge.json")

def load_knowledge():
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "r") as f:
            return json.load(f)
    return {"personal": {}, "preferences": {}, "tasks": [], "facts": []}

def save_knowledge(knowledge):
    with open(KNOWLEDGE_FILE, "w") as f:
        json.dump(knowledge, f, indent=2)

def extract_facts(conversation):
    try:
        prompt = f"""
        Analyze this conversation and extract key facts about the user.
        Return ONLY a JSON object with these exact keys:
        {{
            "personal": {{"name": "", "age": "", "location": "", "occupation": ""}},
            "preferences": {{"likes": [], "dislikes": [], "hobbies": []}},
            "facts": ["fact1", "fact2"]
        }}
        Only include fields that are clearly mentioned. Leave others empty.
        Conversation: {conversation}
        Return ONLY the JSON, no other text.
        """
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        raw = response.choices[0].message.content
        clean = raw.replace("```json", "").replace("```", "").strip()
        new_facts = json.loads(clean)
        
        knowledge = load_knowledge()
        
        # Merge personal info
        for key, value in new_facts.get("personal", {}).items():
            if value:
                knowledge["personal"][key] = value
        
        # Merge preferences
        for key, value in new_facts.get("preferences", {}).items():
            if value:
                if key not in knowledge["preferences"]:
                    knowledge["preferences"][key] = []
                for item in value:
                    if item and item not in knowledge["preferences"][key]:
                        knowledge["preferences"][key].append(item)
        
        # Merge facts
        for fact in new_facts.get("facts", []):
            if fact and fact not in knowledge["facts"]:
                knowledge["facts"].append(fact)
        
        save_knowledge(knowledge)
    except Exception as e:
        print(f"Fact extraction error: {e}")

def build_context():
    knowledge = load_knowledge()
    context = ""
    
    if knowledge["personal"]:
        personal = {k: v for k, v in knowledge["personal"].items() if v}
        if personal:
            context += f"User info: {personal}. "
    
    if knowledge["preferences"]:
        prefs = {k: v for k, v in knowledge["preferences"].items() if v}
        if prefs:
            context += f"User preferences: {prefs}. "
    
    if knowledge["facts"]:
        context += f"Known facts: {', '.join(knowledge['facts'][-5:])}. "
    
    return context

def show_knowledge():
    knowledge = load_knowledge()
    log("=" * 40, "#00ffff")
    log("📚 KIRA'S KNOWLEDGE BASE", "#00ffff")
    log("=" * 40, "#00ffff")
    
    if knowledge["personal"]:
        log("👤 Personal:", "#ffff00")
        for k, v in knowledge["personal"].items():
            if v:
                log(f"   {k}: {v}", "#ffffff")
    
    if knowledge["preferences"]:
        log("❤️ Preferences:", "#ffff00")
        for k, v in knowledge["preferences"].items():
            if v:
                log(f"   {k}: {', '.join(v)}", "#ffffff")
    
    if knowledge["facts"]:
        log("📌 Facts:", "#ffff00")
        for fact in knowledge["facts"]:
            log(f"   • {fact}", "#ffffff")
    
    log("=" * 40, "#00ffff")
    speak("Here's what I know about you!")

# ── GUI Setup ──────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.configure(fg_color="#2b2b2b")
app.title("KIRA — Kinetic Intelligence & Response Assistant")
app.geometry("800x600")
app.resizable(False, False)

# Header
header = ctk.CTkLabel(
    app,
    text="◈ KIRA SYSTEM ONLINE ◈",
    font=ctk.CTkFont(family="Courier", size=20, weight="bold"),
    text_color="#00ffff"
)
header.pack(pady=(20, 5))

subtitle = ctk.CTkLabel(
    app,
    text="Kinetic Intelligence & Response Assistant",
    font=ctk.CTkFont(family="Courier", size=11),
    text_color="#005f5f"
)
subtitle.pack(pady=(0, 10))

# Terminal output box
terminal = ctk.CTkTextbox(
    app,
    width=860,
    height=280,
    font=ctk.CTkFont(family="Courier", size=13),
    fg_color="#0a0a0a",
    text_color="#00ff99",
    border_color="#00ffff",
    border_width=1,
    wrap="word"
)
terminal.pack(padx=20, pady=(0, 10))
terminal.configure(state="disabled")

# Input area
input_frame = ctk.CTkFrame(app, fg_color="transparent")
input_frame.pack(padx=20, fill="x")

input_box = ctk.CTkEntry(
    input_frame,
    placeholder_text="Enter command...",
    font=ctk.CTkFont(family="Courier", size=13),
    fg_color="#0a0a0a",
    border_color="#00ffff",
    text_color="#00ff99",
    height=40
)
input_box.pack(side="left", fill="x", expand=True, padx=(0, 10))

send_btn = ctk.CTkButton(
    input_frame,
    text="EXECUTE",
    font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
    fg_color="#003333",
    hover_color="#005555",
    border_color="#00ffff",
    border_width=1,
    text_color="#00ffff",
    width=100,
    height=40
)
send_btn.pack(side="right")

# Status bar
status = ctk.CTkLabel(
    app,
    text="● SYSTEM READY",
    font=ctk.CTkFont(family="Courier", size=10),
    text_color="#00ff99"
)
status.pack(pady=(5, 0))

# ── Core Functions ─────────────────────────────────────────
def log(text, color="#00ff99"):
    terminal.configure(state="normal")
    terminal.insert("end", text + "\n")
    terminal.see("end")
    terminal.configure(state="disabled")

def listen():
    status.configure(text="● LISTENING...", text_color="#ffff00")
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.pause_threshold = 1
            audio = r.listen(source)
        query = r.recognize_google(audio, language="en-in").lower()
        log(f"YOU ▶ {query}", "#ffffff")
        status.configure(text="● SYSTEM READY", text_color="#00ff99")
        return query
    except:
        speak("Sorry, I didn't catch that.")
        status.configure(text="● SYSTEM READY", text_color="#00ff99")
        return None
    
def speak(text):
    log(f"KIRA ▶ {text}", "#00ffff")
    update_overlay_message(text)
    def _speak():
        try:
            set_orb_mode("speaking")
            asyncio.run(_async_speak(text))
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load("E:\\KIRA\\temp_speech.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)
            pygame.mixer.quit()
            set_orb_mode("idle")
        except Exception as e:
            print(f"TTS error: {e}")
    threading.Thread(target=_speak, daemon=True).start()

def ask_kira(prompt):
    # Build smart context
    context = build_context()
    
    # Inject context into system message
    messages = [
        {
            "role": "system",
            "content": f"You are KIRA (Kinetic Intelligence & Response Assistant), a helpful, smart and friendly AI assistant. Keep responses concise and clear. {context}"
        }
    ] + conversation_history[1:]  # Skip old system message
    
    messages.append({"role": "user", "content": prompt})
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=500
    )
    reply = response.choices[0].message.content
    
    conversation_history.append({"role": "user", "content": prompt})
    conversation_history.append({"role": "assistant", "content": reply})
    save_memory(conversation_history)
    
    # Extract facts in background
    recent = f"User: {prompt}\nKIRA: {reply}"
    threading.Thread(target=extract_facts, args=(recent,), daemon=True).start()
    
    return reply

def send_email(to, subject, body):
    try:
        sender = os.getenv("EMAIL_ADDRESS")
        password = os.getenv("EMAIL_PASSWORD")
        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, to, msg.as_string())
        server.quit()
        speak(f"Email sent successfully to {to}!")
    except Exception as e:
        speak("Sorry, I couldn't send the email.")
        log(f"Email error: {e}", "#ff0000")

def get_weather(city):
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        data = requests.get(url).json()
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            speak(f"Weather in {city}: {description}. Temp: {temp}°C, feels like {feels_like}°C. Humidity: {humidity}%.")
        else:
            speak("Sorry, I couldn't find weather for that city.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the weather.")
        log(f"Weather error: {e}", "#ff0000")

def get_news():
    try:
        api_key = os.getenv("NEWS_API_KEY")
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={api_key}&pageSize=5"
        data = requests.get(url).json()
        articles = data.get("articles", [])
        if articles:
            speak(f"Here are the top {len(articles)} headlines:")
            for i, article in enumerate(articles, 1):
                speak(f"Headline {i}: {article['title']}")
        else:
            speak("Sorry, couldn't fetch news right now.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the news.")
        log(f"News error: {e}", "#ff0000")

def save_note(note):
    try:
        notes_path = os.path.join(os.path.expanduser("~"), "Documents", "KIRA_Notes.txt")
        with open(notes_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            f.write(f"[{timestamp}] {note}\n")
        speak("Note saved successfully!")
    except Exception as e:
        speak("Sorry, I couldn't save the note.")
        log(f"Note error: {e}", "#ff0000")

CALENDAR_FILE = os.path.join(os.path.expanduser("~"), "Documents", "kira_calendar.json")

def load_calendar():
    if os.path.exists(CALENDAR_FILE):
        with open(CALENDAR_FILE, "r") as f:
            return json.load(f)
    return []

def save_calendar(events):
    with open(CALENDAR_FILE, "w") as f:
        json.dump(events, f, indent=2)

def add_event(title, date, time):
    events = load_calendar()
    event = {
        "title": title,
        "date": date,
        "time": time
    }
    events.append(event)
    save_calendar(events)
    speak(f"Event '{title}' added for {date} at {time}!")

def show_today_events():
    events = load_calendar()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_events = [e for e in events if e["date"] == today]
    if today_events:
        speak(f"You have {len(today_events)} event(s) today:")
        for e in today_events:
            speak(f"{e['time']} — {e['title']}")
            log(f"📅 {e['time']} — {e['title']}", "#ffff00")
    else:
        speak("You have no events today!")

def show_all_events():
    events = load_calendar()
    if events:
        speak(f"You have {len(events)} total event(s):")
        for e in events:
            msg = f"{e['date']} at {e['time']} — {e['title']}"
            log(f"📅 {msg}", "#ffff00")
            speak(msg)
        speak("Your calendar is empty!")

def delete_event(title):
    events = load_calendar()
    new_events = [e for e in events if title.lower() not in e["title"].lower()]
    if len(new_events) < len(events):
        save_calendar(new_events)
        speak(f"Event '{title}' deleted!")
    else:
        speak(f"No event found with the name '{title}'")

def file_manager(action, path, extra=""):
    try:
        if action == "list":
            items = os.listdir(path)
            if items:
                speak(f"Found {len(items)} items in {path}:")
                for item in items:
                    log(f"📄 {item}", "#ffff00")
            else:
                speak("Folder is empty!")

        elif action == "delete":
            if os.path.exists(path):
                os.remove(path)
                speak(f"Deleted {os.path.basename(path)} successfully!")
            else:
                speak("File not found!")

        elif action == "mkdir":
            os.makedirs(path, exist_ok=True)
            speak(f"Folder {path} created successfully!")

        elif action == "rename":
            folder = os.path.dirname(path)
            new_path = os.path.join(folder, extra)
            os.rename(path, new_path)
            speak(f"Renamed to {extra} successfully!")

        elif action == "move":
            import shutil
            shutil.move(path, extra)
            speak(f"Moved successfully!")

    except Exception as e:
        speak("Sorry, I couldn't complete that file operation.")
        log(f"File error: {e}", "#ff0000")

import pytesseract
from PIL import ImageGrab

# Set tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def read_screen():
    try:
        speak("Let me look at your screen...")
        screenshot = ImageGrab.grab()
        text = pytesseract.image_to_string(screenshot)
        if text.strip():
            log("=" * 40, "#00ffff")
            log("👁️ SCREEN CONTENT:", "#00ffff")
            log(text[:500], "#ffffff")  # Show first 500 chars
            log("=" * 40, "#00ffff")
            speak("I can see text on your screen. Here's what I found.")
            
            # Ask KIRA to summarize
            summary = ask_kira(f"Summarize this screen content briefly: {text[:1000]}")
            speak(summary)
        else:
            speak("I couldn't find any readable text on your screen.")
    except Exception as e:
        speak("Sorry, I couldn't read your screen.")
        log(f"Screen read error: {e}", "#ff0000")

def analyze_screen_question(question):
    try:
        speak("Analyzing your screen...")
        screenshot = ImageGrab.grab()
        text = pytesseract.image_to_string(screenshot)
        if text.strip():
            prompt = f"Based on this screen content: {text[:1000]}\n\nAnswer this question: {question}"
            answer = ask_kira(prompt)
            speak(answer)
        else:
            speak("I couldn't read enough from your screen to answer that.")
    except Exception as e:
        speak("Sorry, I couldn't analyze your screen.")
        log(f"Screen analyze error: {e}", "#ff0000")

def describe_screen():
    try:
        speak("Taking a look at your screen...")
        screenshot = ImageGrab.grab()
        # Save temp screenshot
        temp_path = "E:\\KIRA\\temp_screen.png"
        screenshot.save(temp_path)
        text = pytesseract.image_to_string(screenshot)
        prompt = f"Describe what appears to be on a computer screen based on this extracted text: {text[:1000]}. Be brief and natural."
        description = ask_kira(prompt)
        speak(description)
        log(f"👁️ {description}", "#00ffff")
    except Exception as e:
        speak("Sorry, I couldn't describe your screen.")
        log(f"Screen describe error: {e}", "#ff0000")

GAMES_FILE = "E:\\KIRA\\kira_games.json"

def load_games():
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE, "r") as f:
            return json.load(f)
    return {}

def launch_game(game_name):
    games = load_games()
    matched = None
    for key in games:
        if key.lower() in game_name.lower() or game_name.lower() in key.lower():
            matched = key
            break
    if matched:
        path = games[matched]
        if os.path.exists(path):
            speak(f"Launching {matched}! Have fun!")
            subprocess.Popen(path)
            start_tracking(matched)
        else:
            speak(f"I found {matched} but couldn't locate the file. Check the path!")
    else:
        speak(f"I don't know where {game_name} is installed. Add it to kira_games.json!")

def list_games():
    games = load_games()
    if games:
        speak(f"I know {len(games)} games:")
        for game in games:
            log(f"🎮 {game}", "#ffff00")
        speak("Check the terminal for the full list!")
    else:
        speak("No games added yet. Edit kira_games.json to add your games!")

def add_game(name, path):
    games = load_games()
    games[name.lower()] = path
    with open(GAMES_FILE, "w") as f:
        json.dump(games, f, indent=2)
    speak(f"Added {name} to my games list!")

STATS_FILE = "E:\\KIRA\\kira_game_stats.json"

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def start_tracking(game_name):
    app._current_game = game_name
    app._game_start_time = datetime.datetime.now()
    log(f"🎮 Tracking session for {game_name}...", "#ffff00")

def stop_tracking():
    if not getattr(app, '_current_game', None):
        speak("No game session is being tracked!")
        return
    
    game = app._current_game
    start = app._game_start_time
    end = datetime.datetime.now()
    duration = (end - start).seconds // 60  # minutes

    stats = load_stats()
    if game not in stats:
        stats[game] = {
            "total_minutes": 0,
            "sessions": 0,
            "last_played": "",
            "longest_session": 0
        }

    stats[game]["total_minutes"] += duration
    stats[game]["sessions"] += 1
    stats[game]["last_played"] = end.strftime("%Y-%m-%d %I:%M %p")
    if duration > stats[game]["longest_session"]:
        stats[game]["longest_session"] = duration

    save_stats(stats)
    app._current_game = None
    speak(f"Session ended! You played {game} for {duration} minutes!")

def show_stats(game_name=None):
    stats = load_stats()
    if not stats:
        speak("No game stats recorded yet!")
        return

    log("=" * 40, "#00ffff")
    log("🎮 GAME STATS", "#00ffff")
    log("=" * 40, "#00ffff")

    if game_name:
        matched = None
        for key in stats:
            if game_name.lower() in key.lower():
                matched = key
                break
        if matched:
            s = stats[matched]
            hours = s["total_minutes"] // 60
            mins = s["total_minutes"] % 60
            log(f"🎮 {matched.upper()}", "#ffff00")
            log(f"   ⏱️ Total: {hours}h {mins}m", "#ffffff")
            log(f"   🔄 Sessions: {s['sessions']}", "#ffffff")
            log(f"   📅 Last played: {s['last_played']}", "#ffffff")
            log(f"   🏆 Longest: {s['longest_session']} mins", "#ffffff")
            speak(f"You've played {matched} for {hours} hours and {mins} minutes across {s['sessions']} sessions!")
        else:
            speak(f"No stats found for {game_name}!")
    else:
        most_played = max(stats, key=lambda x: stats[x]["total_minutes"])
        for game, s in stats.items():
            hours = s["total_minutes"] // 60
            mins = s["total_minutes"] % 60
            log(f"🎮 {game}: {hours}h {mins}m | {s['sessions']} sessions", "#ffff00")
        speak(f"Your most played game is {most_played}!")

import psutil

# ── Gaming Overlay ─────────────────────────────────────────
overlay = None
overlay_running = False

def create_overlay():
    global overlay, overlay_running

    if overlay_running:
        speak("Overlay is already running!")
        return

    overlay = ctk.CTkToplevel(app)
    overlay.title("")
    overlay.geometry("250x180+10+10")  # Top left corner
    overlay.attributes("-topmost", True)  # Always on top
    overlay.attributes("-alpha", 0.85)  # Slightly transparent
    overlay.overrideredirect(True)  # No title bar
    overlay.configure(fg_color="#0a0a0a")
    overlay_running = True

    # Header
    overlay_header = ctk.CTkLabel(
        overlay,
        text="◈ KIRA OVERLAY ◈",
        font=ctk.CTkFont(family="Courier", size=10, weight="bold"),
        text_color="#00ffff"
    )
    overlay_header.pack(pady=(5, 0))

    # Time label
    overlay_time = ctk.CTkLabel(
        overlay,
        text="",
        font=ctk.CTkFont(family="Courier", size=11),
        text_color="#00ff99"
    )
    overlay_time.pack()

    # Session timer
    overlay_session = ctk.CTkLabel(
        overlay,
        text="",
        font=ctk.CTkFont(family="Courier", size=10),
        text_color="#ffff00"
    )
    overlay_session.pack()

    # CPU/RAM
    overlay_system = ctk.CTkLabel(
        overlay,
        text="",
        font=ctk.CTkFont(family="Courier", size=10),
        text_color="#ff9900"
    )
    overlay_system.pack()

    # KIRA message
    overlay_msg = ctk.CTkLabel(
        overlay,
        text="KIRA ready!",
        font=ctk.CTkFont(family="Courier", size=10),
        text_color="#ffffff",
        wraplength=230
    )
    overlay_msg.pack(pady=(5, 0))

    # Close button
    close_btn = ctk.CTkButton(
        overlay,
        text="✕",
        width=20,
        height=20,
        fg_color="#330000",
        hover_color="#550000",
        text_color="#ff0000",
        command=close_overlay
    )
    close_btn.pack(pady=(5, 0))

    # Make overlay draggable
    def start_drag(event):
        overlay._drag_start_x = event.x
        overlay._drag_start_y = event.y

    def do_drag(event):
        x = overlay.winfo_x() + event.x - overlay._drag_start_x
        y = overlay.winfo_y() + event.y - overlay._drag_start_y
        overlay.geometry(f"+{x}+{y}")

    overlay.bind("<Button-1>", start_drag)
    overlay.bind("<B1-Motion>", do_drag)

    # Store references
    app._overlay_time = overlay_time
    app._overlay_session = overlay_session
    app._overlay_system = overlay_system
    app._overlay_msg = overlay_msg

    speak("Gaming overlay activated!")
    update_overlay()

def update_overlay():
    global overlay_running
    if not overlay_running or not overlay:
        return
    try:
        # Time
        now = datetime.datetime.now().strftime("%I:%M:%S %p")
        app._overlay_time.configure(text=f"🕐 {now}")

        # Session timer
        if getattr(app, '_game_start_time', None):
            elapsed = datetime.datetime.now() - app._game_start_time
            mins = elapsed.seconds // 60
            secs = elapsed.seconds % 60
            game = getattr(app, '_current_game', 'Unknown')
            app._overlay_session.configure(text=f"🎮 {game}: {mins:02d}:{secs:02d}")
        else:
            app._overlay_session.configure(text="🎮 No game running")

        # CPU/RAM
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        app._overlay_system.configure(text=f"💻 CPU: {cpu}% | RAM: {ram}%")

        overlay.after(1000, update_overlay)
    except:
        overlay_running = False

def close_overlay():
    global overlay, overlay_running
    overlay_running = False
    if overlay:
        overlay.destroy()
        overlay = None
    speak("Overlay closed!")

def update_overlay_message(msg):
    if overlay_running and overlay:
        try:
            app._overlay_msg.configure(text=f"KIRA: {msg[:50]}")
        except:
            pass

def game_assistant(query, game=None):
    try:
        current_game = game or getattr(app, '_current_game', None)
        if current_game:
            prompt = f"You are a game expert for {current_game}. Answer this question briefly and helpfully: {query}"
        else:
            prompt = f"You are a gaming expert. Answer this question briefly and helpfully: {query}"
        
        speak("Let me check that for you...")
        response = ask_kira(prompt)
        speak(response)
        log(f"🎮 {response}", "#ffff00")
    except Exception as e:
        speak("Sorry, I couldn't find an answer for that.")
        log(f"Game assistant error: {e}", "#ff0000")

def get_game_tips(game_name):
    try:
        game = game_name or getattr(app, '_current_game', None)
        if not game:
            speak("Which game do you need tips for?")
            return
        prompt = f"Give me 3 quick beginner tips for {game}. Keep each tip under 2 sentences."
        speak(f"Here are some tips for {game}!")
        response = ask_kira(prompt)
        speak(response)
        log(f"💡 {response}", "#ffff00")
    except Exception as e:
        speak("Sorry, couldn't fetch tips right now.")

def get_walkthrough(game_name, situation):
    try:
        game = game_name or getattr(app, '_current_game', None)
        if not game:
            speak("Which game do you need help with?")
            return
        prompt = f"In {game}, help me with this situation: {situation}. Give a brief, clear solution."
        speak("Let me help you get through this!")
        response = ask_kira(prompt)
        speak(response)
        log(f"🗺️ {response}", "#ffff00")
    except Exception as e:
        speak("Sorry, couldn't fetch walkthrough right now.")

import threading

REMINDERS_FILE = "E:\\KIRA\\kira_reminders.json"

def load_reminders():
    if os.path.exists(REMINDERS_FILE):
        with open(REMINDERS_FILE, "r") as f:
            return json.load(f)
    return []

def save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f:
        json.dump(reminders, f, indent=2)

def set_reminder(message, minutes):
    try:
        remind_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        reminders = load_reminders()
        reminder = {
            "message": message,
            "time": remind_time.strftime("%Y-%m-%d %H:%M:%S"),
            "done": False
        }
        reminders.append(reminder)
        save_reminders(reminders)
        speak(f"Reminder set! I'll remind you in {minutes} minutes.")
        log(f"🔔 Reminder set for {remind_time.strftime('%I:%M %p')}: {message}", "#ffff00")

        def trigger():
            import time
            time.sleep(minutes * 60)
            speak(f"Reminder! {message}")
            log(f"🔔 REMINDER: {message}", "#ff9900")

        threading.Thread(target=trigger, daemon=True).start()
    except Exception as e:
        speak("Sorry, I couldn't set that reminder.")
        log(f"Reminder error: {e}", "#ff0000")

def show_reminders():
    reminders = load_reminders()
    pending = [r for r in reminders if not r["done"]]
    if pending:
        speak(f"You have {len(pending)} pending reminder(s):")
        log("=" * 40, "#00ffff")
        log("🔔 PENDING REMINDERS", "#00ffff")
        log("=" * 40, "#00ffff")
        for i, r in enumerate(pending, 1):
            log(f"{i}. {r['time']} — {r['message']}", "#ffff00")
    else:
        speak("You have no pending reminders!")

def cancel_reminder(keyword):
    reminders = load_reminders()
    new_reminders = [r for r in reminders if keyword.lower() not in r["message"].lower()]
    if len(new_reminders) < len(reminders):
        save_reminders(new_reminders)
        speak(f"Reminder cancelled!")
    else:
        speak(f"No reminder found with that keyword!")

def translate_text(text, target_language):
    try:
        speak(f"Translating to {target_language}...")
        prompt = f"Translate this text to {target_language}. Return ONLY the translated text, nothing else: {text}"
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        translation = response.choices[0].message.content.strip()
        speak(f"Translation: {translation}")
        log("=" * 40, "#00ffff")
        log(f"🌍 TRANSLATION ({target_language})", "#00ffff")
        log(f"Original: {text}", "#ffffff")
        log(f"Translated: {translation}", "#ffff00")
        log("=" * 40, "#00ffff")
    except Exception as e:
        speak("Sorry, I couldn't translate that.")
        log(f"Translation error: {e}", "#ff0000")
    
from bs4 import BeautifulSoup

def scrape_website(url):
    try:
        speak("Let me read that website for you...")
        headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate",
                    "Connection": "keep-alive",
                  }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = " ".join(chunk for chunk in chunks if chunk)[:2000]

        log("=" * 40, "#00ffff")
        log("🌐 WEBSITE CONTENT", "#00ffff")
        log("=" * 40, "#00ffff")
        log(clean_text[:500], "#ffffff")
        log("=" * 40, "#00ffff")

        summary = ask_kira(f"Summarize this webpage content in 3 sentences: {clean_text}")
        speak(summary)
        log(f"📝 Summary: {summary}", "#ffff00")

    except Exception as e:
        speak("Sorry, I couldn't read that website.")
        log(f"Scrape error: {e}", "#ff0000")

def scrape_price(url):
    try:
        speak("Let me check that price for you...")
        headers = headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.5",
                                "Accept-Encoding": "gzip, deflate",
                                "Connection": "keep-alive",
                            }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove scripts
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        clean_text = " ".join(line for line in lines if line)[:2000]

        price_info = ask_kira(f"Extract the product name and price from this webpage text. Be brief: {clean_text}")
        speak(price_info)
        log(f"💰 {price_info}", "#ffff00")

    except Exception as e:
        speak("Sorry, I couldn't check that price.")
        log(f"Price check error: {e}", "#ff0000")

def summarize_article(url):
    try:
        speak("Reading and summarizing that article...")
        headers = headers = {
                                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                "Accept-Language": "en-US,en;q=0.5",
                                "Accept-Encoding": "gzip, deflate",
                                "Connection": "keep-alive",
                            }
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")

        # Get article paragraphs
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])[:3000]

        if text.strip():
            summary = ask_kira(f"Summarize this article in 5 sentences: {text}")
            speak(summary)
            log("=" * 40, "#00ffff")
            log("📰 ARTICLE SUMMARY", "#00ffff")
            log("=" * 40, "#00ffff")
            log(summary, "#ffff00")
        else:
            speak("I couldn't extract article content from that page.")

    except Exception as e:
        speak("Sorry, I couldn't summarize that article.")
        log(f"Article error: {e}", "#ff0000")

import pywhatkit

def send_whatsapp(phone, message, hour, minute):
    try:
        speak(f"Sending WhatsApp message in a moment...")
        log(f"📱 Sending WhatsApp to {phone} at {hour}:{minute:02d}", "#ffff00")
        pywhatkit.sendwhatmsg(phone, message, hour, minute, wait_time=15, tab_close=True)
        speak("WhatsApp message sent successfully!")
    except Exception as e:
        speak("Sorry, I couldn't send that WhatsApp message.")
        log(f"WhatsApp error: {e}", "#ff0000")

def send_whatsapp_now(phone, message):
    try:
        speak("Sending WhatsApp message now...")
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute + 2  # 2 minutes from now
        if minute >= 60:
            minute -= 60
            hour += 1
        pywhatkit.sendwhatmsg(phone, message, hour, minute, wait_time=15, tab_close=True)
        speak("WhatsApp message sent!")
    except Exception as e:
        speak("Sorry, I couldn't send that WhatsApp message.")
        log(f"WhatsApp error: {e}", "#ff0000")

def generate_image(prompt):
    try:
        speak(f"Generating image, please wait...")
        log(f"🎨 Generating: {prompt}", "#ffff00")
        
        encoded_prompt = prompt.replace(" ", "%20")
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"
        
        response = requests.get(url, timeout=60)  # increased to 60 seconds
        if response.status_code == 200:
            img_path = "E:\\KIRA\\kira_generated.png"
            with open(img_path, "wb") as f:
                f.write(response.content)
            speak("Image generated! Opening it now!")
            log(f"🎨 Image saved!", "#ffff00")
            os.startfile(img_path)
        else:
            speak("Sorry, I couldn't generate that image.")
    except Exception as e:
        speak("Sorry, image generation failed. Try again!")
        log(f"Image error: {e}", "#ff0000")

def handle_command(query):
    if not query:
        return
    set_orb_mode("processing")
    status.configure(text="● PROCESSING...", text_color="#ff9900")

    if "open notepad" in query:
        speak("Opening Notepad")
        subprocess.Popen("notepad.exe")
    elif "open calculator" in query:
        speak("Opening Calculator")
        subprocess.Popen("calc.exe")
    elif "open chrome" in query:
        speak("Opening Chrome")
        subprocess.Popen("chrome.exe")
    elif "open vs code" in query or "open vscode" in query:
        speak("Opening VS Code")
        subprocess.Popen("code")
    elif "open file manager" in query or "open explorer" in query:
        speak("Opening File Explorer")
        subprocess.Popen("explorer.exe")
    elif "open task manager" in query:
        speak("Opening Task Manager")
        subprocess.Popen("taskmgr.exe")
    elif "open settings" in query:
        speak("Opening Settings")
        subprocess.Popen("ms-settings:", shell=True)
    elif "volume up" in query:
        speak("Turning volume up")
        for _ in range(5):
            subprocess.call(["nircmd.exe", "changesysvolume", "5000"])
    elif "volume down" in query:
        speak("Turning volume down")
        for _ in range(5):
            subprocess.call(["nircmd.exe", "changesysvolume", "-5000"])
    elif "mute" in query:
        speak("Muting")
        subprocess.call(["nircmd.exe", "mutesysvolume", "1"])
    elif "unmute" in query:
        speak("Unmuting")
        subprocess.call(["nircmd.exe", "mutesysvolume", "0"])
    elif "shutdown" in query:
        speak("Shutting down in 10 seconds!")
        subprocess.Popen("shutdown /s /t 10", shell=True)
    elif "restart" in query:
        speak("Restarting in 10 seconds!")
        subprocess.Popen("shutdown /r /t 10", shell=True)
    elif "cancel shutdown" in query:
        speak("Shutdown cancelled!")
        subprocess.Popen("shutdown /a", shell=True)
    elif "lock" in query:
        speak("Locking the computer")
        subprocess.call("rundll32.exe user32.dll,LockWorkStation", shell=True)
    elif "take screenshot" in query:
        ss_path = os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots", "screenshot.png")
        pyautogui.screenshot(ss_path)
        speak("Screenshot saved!")
    elif "search" in query:
        term = query.replace("search", "").strip()
        speak(f"Searching for {term}")
        webbrowser.open(f"https://www.google.com/search?q={term}")
    elif "play" in query:
        song = query.replace("play", "").strip()
        speak(f"Playing {song} on YouTube")
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
    elif "time" in query:
        time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"Current time is {time}")
    elif "date" in query:
        date = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today is {date}")
    elif "save note" in query or "take note" in query:
        speak("What should I note down?")
        log("KIRA ▶ Type your note in the input box and press EXECUTE", "#00ffff")
        app.after(100, lambda: setattr(app, '_note_mode', True))
    elif "weather" in query:
        if "in" in query:
            city = query.split("in")[-1].strip()
        else:
            city = "Hyderabad"
        get_weather(city)
    elif "news" in query or "headlines" in query:
        get_news()
    elif "send email" in query or "send mail" in query:
        speak("Please type: to|subject|message in the input box")
        log("KIRA ▶ Format: recipient@email.com|Subject|Message body", "#00ffff")
    elif "clear memory" in query or "forget everything" in query:
        conversation_history.clear()
        conversation_history.append({"role": "system", "content": "You are KIRA (Kinetic Intelligence & Response Assistant), a helpful, smart and friendly AI assistant. Keep responses concise and clear."})
        save_memory(conversation_history)
        speak("Memory cleared! Starting fresh.")
    
    elif "add event" in query or "add to calendar" in query:
        speak("What is the event title?")
        log("KIRA ▶ Type: title|YYYY-MM-DD|HH:MM in the input box", "#00ffff")
        app.after(100, lambda: setattr(app, '_calendar_mode', True))

    elif "today's events" in query or "what's today" in query:
        show_today_events()

    elif "show calendar" in query or "all events" in query or "show calender" in query or "show events" in query:
        show_all_events()

    elif "delete event" in query:
        title = query.replace("delete event", "").strip()
        if title:
            delete_event(title)
        else:
            speak("Which event should I delete?")
            log("KIRA ▶ Type the event name in the input box", "#00ffff")
            app.after(100, lambda: setattr(app, '_delete_event_mode', True))
    elif any(word in query for word in ["exit", "quit", "bye", "shutdown kira"]):
        speak("Goodbye! KIRA going offline!")
    elif "list files" in query:
        speak("Which folder? Type the path in the input box.")
        log("KIRA ▶ Type full folder path e.g. C:\\Users\\Admin\\Documents", "#00ffff")
        app.after(100, lambda: setattr(app, '_listfiles_mode', True))

    elif "delete file" in query:
        speak("Type the full file path to delete.")
        log("KIRA ▶ Type full file path e.g. C:\\Users\\Admin\\test.txt", "#00ffff")
        app.after(100, lambda: setattr(app, '_deletefile_mode', True))

    elif "create folder" in query:
        speak("Type the full path for the new folder.")
        log("KIRA ▶ Type full path e.g. C:\\Users\\Admin\\NewFolder", "#00ffff")
        app.after(100, lambda: setattr(app, '_mkdir_mode', True))

    elif "rename file" in query:
        speak("Type: old path|new name")
        log("KIRA ▶ Format: C:\\path\\oldname.txt|newname.txt", "#00ffff")
        app.after(100, lambda: setattr(app, '_rename_mode', True))

    elif "what do you know" in query or "show knowledge" in query:
        show_knowledge()

    elif "forget" in query and "memory" not in query:
        fact = query.replace("forget", "").strip()
        knowledge = load_knowledge()
        knowledge["facts"] = [f for f in knowledge["facts"] if fact.lower() not in f.lower()]
        save_knowledge(knowledge)
        speak(f"I've forgotten everything about {fact}!")

    elif "move file" in query:
        speak("Type: source path|destination path")
        log("KIRA ▶ Format: C:\\source\\file.txt|C:\\destination\\", "#00ffff")
        app.after(100, lambda: setattr(app, '_move_mode', True))
        app.after(2000, app.destroy)

    elif "read screen" in query or "read my screen" in query:
        threading.Thread(target=read_screen, daemon=True).start()

    elif "describe screen" in query or "what's on my screen" in query:
        threading.Thread(target=describe_screen, daemon=True).start()

    elif "what does" in query and "screen" in query:
        question = query.replace("screen", "").replace("what does", "").strip()
        threading.Thread(target=lambda: analyze_screen_question(question), daemon=True).start()

    elif "look at screen" in query or "analyze screen" in query:
        threading.Thread(target=describe_screen, daemon=True).start()
    
    elif "launch game" in query or "open game" in query or "play game" in query:
        game = query.replace("launch game", "").replace("open game", "").replace("play game", "").strip()
        if game:
            launch_game(game)
        else:
            speak("Which game should I launch?")
            log("KIRA ▶ Type the game name in the input box", "#00ffff")
            app.after(100, lambda: setattr(app, '_launch_game_mode', True))

    elif "list games" in query or "what games" in query:
        list_games()

    elif "add game" in query:
        speak("Type: game name|full path to exe")
        log("KIRA ▶ Format: minecraft|C:\\path\\to\\game.exe", "#00ffff")
        app.after(100, lambda: setattr(app, '_add_game_mode', True))
    
    elif "game stats" in query or "my stats" in query:
        game = query.replace("game stats", "").replace("my stats", "").strip()
        show_stats(game if game else None)

    elif "stop tracking" in query or "game over" in query or "done playing" in query:
        stop_tracking()

    elif "most played" in query:
        stats = load_stats()
        if stats:
            most = max(stats, key=lambda x: stats[x]["total_minutes"])
            hours = stats[most]["total_minutes"] // 60
            speak(f"Your most played game is {most} with {hours} hours!")
        else:
            speak("No stats yet! Launch a game first.")
    
    elif "open overlay" in query or "gaming overlay" in query or "start overlay" in query:
        app.after(100, create_overlay)

    elif "close overlay" in query or "hide overlay" in query:
        close_overlay()
    
    elif "game tip" in query or "tips for" in query:
        game = query.replace("game tip", "").replace("tips for", "").strip()
        get_game_tips(game if game else None)

    elif "help me with" in query and "game" in query:
        situation = query.replace("help me with", "").replace("game", "").strip()
        get_walkthrough(None, situation)

    elif "how do i" in query or "how to" in query:
        game_assistant(query)

    elif "game strategy" in query or "best strategy" in query:
        game_assistant(query)

    elif "game bug" in query or "game not working" in query:
        game_assistant(query)
    
    elif "remind me" in query or "set reminder" in query:
        speak("What should I remind you about?")
        log("KIRA ▶ Type: message|minutes (e.g. drink water|30)", "#00ffff")
        app.after(100, lambda: setattr(app, '_reminder_mode', True))

    elif "show reminders" in query or "my reminders" in query:
        show_reminders()

    elif "cancel reminder" in query:
        keyword = query.replace("cancel reminder", "").strip()
        if keyword:
            cancel_reminder(keyword)
        else:
            speak("Which reminder should I cancel?")
            log("KIRA ▶ Type the reminder keyword", "#00ffff")
            app.after(100, lambda: setattr(app, '_cancel_reminder_mode', True))
    
    elif "translate" in query:
        speak("Type: text|language")
        log("KIRA ▶ Format: Hello how are you|Spanish", "#00ffff")
        app.after(100, lambda: setattr(app, '_translate_mode', True))

    elif "how do you say" in query:
        # e.g. "how do you say hello in Japanese"
        parts = query.replace("how do you say", "").strip()
        if " in " in parts:
            text, lang = parts.split(" in ", 1)
            translate_text(text.strip(), lang.strip())
        else:
            speak("Please say: how do you say [word] in [language]")
    
    elif "read website" in query or "scrape" in query:
        speak("Paste the website URL in the input box!")
        log("KIRA ▶ Type the full URL (e.g. https://example.com)", "#00ffff")
        app.after(100, lambda: setattr(app, '_scrape_mode', True))

    elif "check price" in query or "price of" in query:
        speak("Paste the product URL in the input box!")
        log("KIRA ▶ Type the full product URL", "#00ffff")
        app.after(100, lambda: setattr(app, '_price_mode', True))

    elif "summarize article" in query or "summarize this" in query:
        speak("Paste the article URL in the input box!")
        log("KIRA ▶ Type the full article URL", "#00ffff")
        app.after(100, lambda: setattr(app, '_article_mode', True))
    
    elif "whatsapp" in query or "send whatsapp" in query:
        speak("Type: phone|message")
        log("KIRA ▶ Format: +919876543210|Hey how are you?", "#00ffff")
        log("KIRA ▶ Phone must start with country code e.g. +91 for India", "#00ffff")
        app.after(100, lambda: setattr(app, '_whatsapp_mode', True))

    elif "generate image" in query or "create image" in query or "draw" in query:
        prompt = query.replace("generate image", "").replace("create image", "").replace("draw", "").strip()
        if not prompt or len(prompt) < 3:
            speak("What should I generate?")
            log("KIRA ▶ Type your image description in the input box", "#00ffff")
            app.after(100, lambda: setattr(app, '_image_mode', True))
            return
        if prompt:
            threading.Thread(target=generate_image, args=(prompt,), daemon=True).start()
        else:
            speak("What should I generate?")
            log("KIRA ▶ Type your image description in the input box", "#00ffff")
            app.after(100, lambda: setattr(app, '_image_mode', True))

    else:
        speak("Let me think...")
        threading.Thread(target=lambda: speak(ask_kira(query)), daemon=True).start()

    set_orb_mode("idle")
    status.configure(text="● SYSTEM READY", text_color="#00ff99")

def process_input(event=None):
    query = input_box.get().strip()
    if not query:
        return
    
    if getattr(app, '_image_mode', False):
        app._image_mode = False
        input_box.delete(0, "end")
        threading.Thread(target=generate_image, args=(query,), daemon=True).start()
        return
    
    if getattr(app, '_whatsapp_mode', False):
        app._whatsapp_mode = False
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 2:
            phone = parts[0].strip()
            message = parts[1].strip()
            threading.Thread(target=send_whatsapp_now, args=(phone, message), daemon=True).start()
        else:
            speak("Please use format: phone|message")
        return

    if getattr(app, '_scrape_mode', False):
        app._scrape_mode = False
        input_box.delete(0, "end")
        threading.Thread(target=scrape_website, args=(query,), daemon=True).start()
        return

    if getattr(app, '_price_mode', False):
        app._price_mode = False
        input_box.delete(0, "end")
        threading.Thread(target=scrape_price, args=(query,), daemon=True).start()
        return

    if getattr(app, '_article_mode', False):
        app._article_mode = False
        input_box.delete(0, "end")
        threading.Thread(target=summarize_article, args=(query,), daemon=True).start()
        return
    
    if getattr(app, '_translate_mode', False):
        app._translate_mode = False
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 2:
            translate_text(parts[0].strip(), parts[1].strip())
        else:
            speak("Please use format: text|language")
        return
    
    if getattr(app, '_reminder_mode', False):
        app._reminder_mode = False
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 2:
            try:
                set_reminder(parts[0].strip(), int(parts[1].strip()))
            except:
                speak("Please use format: message|minutes")
        else:
            speak("Please use format: message|minutes")
        return

    if getattr(app, '_cancel_reminder_mode', False):
        app._cancel_reminder_mode = False
        input_box.delete(0, "end")
        cancel_reminder(query)
        return
    
    if getattr(app, '_launch_game_mode', False):
        app._launch_game_mode = False
        input_box.delete(0, "end")
        launch_game(query)
        return

    if getattr(app, '_add_game_mode', False):
        app._add_game_mode = False
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 2:
            add_game(parts[0].strip(), parts[1].strip())
        else:
            speak("Please use format: name|path")
        return
    
    if getattr(app, '_listfiles_mode', False):
        app._listfiles_mode = False
        input_box.delete(0, "end")
        file_manager("list", query)
        return

    if getattr(app, '_deletefile_mode', False):
        app._deletefile_mode = False
        input_box.delete(0, "end")
        file_manager("delete", query)
        return

    if getattr(app, '_mkdir_mode', False):
        app._mkdir_mode = False
        input_box.delete(0, "end")
        file_manager("mkdir", query)
        return

    if getattr(app, '_rename_mode', False):
        app._rename_mode = False
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 2:
            file_manager("rename", parts[0].strip(), parts[1].strip())
        return

    if getattr(app, '_move_mode', False):
        app._move_mode = False
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 2:
            file_manager("move", parts[0].strip(), parts[1].strip())
        return
    
    if getattr(app, '_calendar_mode', False):
        app._calendar_mode = False
        log(f"CALENDAR ▶ {query}", "#ffff00")
        input_box.delete(0, "end")
        parts = query.split("|")
        if len(parts) == 3:
            add_event(parts[0].strip(), parts[1].strip(), parts[2].strip())
        else:
            speak("Please use format: title|YYYY-MM-DD|HH:MM")
        return

    if getattr(app, '_delete_event_mode', False):
        app._delete_event_mode = False
        log(f"DELETE ▶ {query}", "#ffff00")
        input_box.delete(0, "end")
        delete_event(query)
        return
    
    if getattr(app, '_note_mode', False):
        app._note_mode = False
        log(f"NOTE ▶ {query}", "#ffff00")
        input_box.delete(0, "end")
        save_note(query)
        return

    log(f"YOU ▶ {query.lower()}", "#ffffff")
    input_box.delete(0, "end")

    if "|" in query:
        parts = query.split("|")
        if len(parts) == 3:
            send_email(parts[0].strip(), parts[1].strip(), parts[2].strip())
        return

    threading.Thread(target=handle_command, args=(query.lower(),), daemon=True).start()

def voice_input():
    threading.Thread(target=lambda: handle_command(listen()), daemon=True).start()

# Bind buttons
send_btn.configure(command=process_input)
input_box.bind("<Return>", process_input)

# Voice button
voice_btn = ctk.CTkButton(
    app,
    text="🎤 VOICE INPUT",
    font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
    fg_color="#003333",
    hover_color="#005555",
    border_color="#00ffff",
    border_width=1,
    text_color="#00ffff",
    width=200,
    height=35,
    command=voice_input
)
voice_btn.pack(pady=(5, 0))

# Orb Canvas - Cyan/Blue Plasma style
orb_canvas = ctk.CTkCanvas(app, width=100, height=100, bg="#2b2b2b", highlightthickness=0)
orb_canvas.pack(pady=(0, 5))

# Wake word toggle
wake_status = {"active": True}

def toggle_wake():
    global wake_listening
    wake_listening = not wake_listening
    wake_status["active"] = wake_listening
    if wake_listening:
        wake_btn.configure(text="👂 WAKE WORD: ON", text_color="#00ff99")
        log("👂 Wake word listener ON", "#00ff99")
    else:
        wake_btn.configure(text="👂 WAKE WORD: OFF", text_color="#ff0000")
        log("👂 Wake word listener OFF", "#ff0000")

wake_btn = ctk.CTkButton(
    app,
    text="👂 WAKE WORD: ON",
    font=ctk.CTkFont(family="Courier", size=12, weight="bold"),
    fg_color="#003333",
    hover_color="#005555",
    border_color="#00ffff",
    border_width=1,
    text_color="#00ff99",
    width=200,
    height=35,
    command=toggle_wake
)
wake_btn.pack(pady=(5, 0))

import math

orb_state = {"mode": "idle", "step": 0, "angle": 0}

def draw_plasma_orb(color_core, color_mid, color_outer, color_ring, angle):
    orb_canvas.delete("all")
    orb_canvas.create_rectangle(0, 0, 100, 100, fill="#2b2b2b", outline="")
    cx, cy, r = 50, 50, 38

    # Outer glow rings
    for i in range(6, 0, -1):
        alpha_r = r + i * 1
        fade = hex(20 + i * 8)[2:].zfill(2)
        orb_canvas.create_oval(
            cx - alpha_r, cy - alpha_r,
            cx + alpha_r, cy + alpha_r,
            fill="", outline=color_ring, width=1
        )

    # Base sphere layers
    for i in range(r, 0, -3):
        ratio = i / r
        orb_canvas.create_oval(
            cx - i, cy - i, cx + i, cy + i,
            fill=color_outer if ratio > 0.7 else (color_mid if ratio > 0.4 else color_core),
            outline=""
        )

    # Animated energy arcs
    for i in range(6):
        arc_angle = angle + i * 60
        x1 = cx + (r - 8) * math.cos(math.radians(arc_angle))
        y1 = cy + (r - 8) * math.sin(math.radians(arc_angle))
        x2 = cx + (r - 5) * math.cos(math.radians(arc_angle + 40))
        y2 = cy + (r - 5) * math.sin(math.radians(arc_angle + 40))
        orb_canvas.create_line(x1, y1, x2, y2, fill=color_ring, width=2, smooth=True)

    # Floating plasma dots
    for i in range(8):
        dot_angle = angle * 1.5 + i * 45
        dot_r = r - 10 + math.sin(math.radians(angle + i * 30)) * 8
        dx = cx + dot_r * math.cos(math.radians(dot_angle))
        dy = cy + dot_r * math.sin(math.radians(dot_angle))
        orb_canvas.create_oval(dx-2, dy-2, dx+2, dy+2, fill=color_ring, outline="")

    # 3D highlight
    orb_canvas.create_oval(cx-15, cy-22, cx-5, cy-12, fill="#aaffff", outline="")
    orb_canvas.create_oval(cx-13, cy-20, cx-8, cy-15, fill="#ffffff", outline="")

def animate_orb():
    mode = orb_state["mode"]
    angle = orb_state["angle"]

    if mode == "idle":
        # Full 360 rotation in 5 seconds
        # 360 degrees / (5000ms / 50ms per frame) = 3.6 degrees per frame
        draw_plasma_orb("#001a33", "#003366", "#0066aa", "#00ccff", angle)
        orb_state["angle"] = (angle + 3.6) % 360
        app.after(50, animate_orb)

    elif mode == "processing":
        # Faster rotation when processing
        draw_plasma_orb("#1a1a00", "#336600", "#66aa00", "#ffff00", angle)
        orb_state["angle"] = (angle + 8) % 360
        app.after(30, animate_orb)

    elif mode == "speaking":
        # Medium rotation when speaking
        draw_plasma_orb("#001a00", "#006633", "#00aa66", "#00ffcc", angle)
        orb_state["angle"] = (angle + 5) % 360
        app.after(40, animate_orb)

def set_orb_mode(mode):
    orb_state["mode"] = mode

animate_orb()

# Startup message
log("=" * 60)
log("  ██╗  ██╗██╗██████╗  █████╗ ")
log("  ██║ ██╔╝██║██╔══██╗██╔══██╗")
log("  █████╔╝ ██║██████╔╝███████║")
log("  ██╔═██╗ ██║██╔══██╗██╔══██║")
log("  ██║  ██╗██║██║  ██║██║  ██║")
log("  ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝  ╚═╝")
log("=" * 60)
log("  KIRA v1.4 — Kinetic Intelligence & Response Assistant")
log("  STATUS: ALL SYSTEMS ONLINE")
log("=" * 60)
log("")

threading.Thread(target=lambda: speak("KIRA online. All systems ready. How can I assist you?"), daemon=True).start()

# ── Always-On Wake Word Listener ───────────────────────────
wake_listening = True

def wake_word_listener():
    r = sr.Recognizer()
    r.energy_threshold = 3000
    r.dynamic_energy_threshold = True
    
    log("👂 Wake word listener active — say 'KIRA sync'!", "#005555")
    
    while wake_listening:
        try:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.3)
                audio = r.listen(source, timeout=3, phrase_time_limit=3)
            
            try:
                text = r.recognize_google(audio, language="en-in").lower()
                if "kira sync" in text or "kira sink" in text or "kira" in text:
                    log("🔔 Wake word detected!", "#00ffff")
                    app.after(0, lambda: speak("Yes? How can I help?"))
                    
                    # Now listen for command
                    with sr.Microphone() as source:
                        r.adjust_for_ambient_noise(source, duration=0.3)
                        log("👂 Listening for command...", "#ffff00")
                        audio2 = r.listen(source, timeout=5, phrase_time_limit=8)
                    
                    try:
                        command = r.recognize_google(audio2, language="en-in").lower()
                        log(f"YOU ▶ {command}", "#ffffff")
                        app.after(0, lambda c=command: handle_command(c))
                    except:
                        app.after(0, lambda: speak("Sorry, I didn't catch that!"))
            except:
                pass
        except:
            pass

# Start wake word listener in background
wake_thread = threading.Thread(target=wake_word_listener, daemon=True)
wake_thread.start()
app.mainloop()
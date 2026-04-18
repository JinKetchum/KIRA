import os
import datetime
import webbrowser
import subprocess
import pyttsx3
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Voice engine setup
engine = pyttsx3.init()
engine.setProperty("rate", 170)
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[1].id)  # Female voice

conversation_history = [
    {
        "role": "system",
        "content": "You are KIRA (Kinetic Intelligence & Response Assistant), a helpful, smart and friendly AI assistant. Keep responses concise and clear."
    }
]

def speak(text):
    print(f"KIRA: {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language="en-in")
        print(f"You: {query}")
        return query.lower()
    except:
        speak("Sorry, I didn't catch that. Please try again.")
        return None

def ask_kira(prompt):
    conversation_history.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=conversation_history,
        max_tokens=500
    )
    reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
        speak("Sorry, I couldn't send the email. Please check your credentials.")
        print(f"Email error: {e}")

import requests

def get_weather(city):
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data["cod"] == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            city_name = data["name"]

            report = (f"Weather in {city_name}: {description}. "
                     f"Temperature is {temp}°C, feels like {feels_like}°C. "
                     f"Humidity is {humidity}%.")
            speak(report)
        else:
            speak("Sorry, I couldn't find weather for that city.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the weather right now.")
        print(f"Weather error: {e}")

def get_news():
    try:
        api_key = os.getenv("NEWS_API_KEY")
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={api_key}&pageSize=5"
        response = requests.get(url)
        data = response.json()

        articles = data.get("articles", [])
        if articles:
            speak(f"Here are the top {len(articles)} news headlines:")
            for i, article in enumerate(articles, 1):
                title = article["title"]
                speak(f"Headline {i}: {title}")
                print(f"{i}. {title}")
        else:
            speak("Sorry, I couldn't fetch the news right now.")
    except Exception as e:
        speak("Sorry, I couldn't fetch the news right now.")
        print(f"News error: {e}")

def save_note(note):
    try:
        notes_path = os.path.join(os.path.expanduser("~"), "Documents", "KIRA_Notes.txt")
        with open(notes_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            f.write(f"[{timestamp}] {note}\n")
        speak("Note saved successfully!")
        print(f"Note saved to: {notes_path}")
    except Exception as e:
        speak("Sorry, I couldn't save the note.")
        print(f"Note error: {e}")

def read_notes():
    try:
        notes_path = os.path.join(os.path.expanduser("~"), "Documents", "KIRA_Notes.txt")
        if os.path.exists(notes_path):
            with open(notes_path, "r") as f:
                notes = f.read()
            if notes:
                speak("Here are your saved notes:")
                print(notes)
                speak(notes)
            else:
                speak("You have no saved notes.")
        else:
            speak("You have no saved notes yet.")
    except Exception as e:
        speak("Sorry, I couldn't read the notes.")
        print(f"Note error: {e}")

def handle_command(query):
    if query is None:
        return

    # Open apps
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
    # Volume control
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

    # System controls
    elif "shutdown" in query:
        speak("Shutting down the computer in 10 seconds!")
        subprocess.Popen("shutdown /s /t 10", shell=True)

    elif "restart" in query:
        speak("Restarting the computer in 10 seconds!")
        subprocess.Popen("shutdown /r /t 10", shell=True)

    elif "cancel shutdown" in query:
        speak("Shutdown cancelled!")
        subprocess.Popen("shutdown /a", shell=True)

    elif "lock" in query:
        speak("Locking the computer")
        subprocess.call("rundll32.exe user32.dll,LockWorkStation", shell=True)

    elif "sleep" in query:
        speak("Going to sleep")
        subprocess.call("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)

    # Open common apps
    elif "open file manager" in query or "open explorer" in query:
        speak("Opening File Explorer")
        subprocess.Popen("explorer.exe")

    elif "open task manager" in query:
        speak("Opening Task Manager")
        subprocess.Popen("taskmgr.exe")

    elif "open settings" in query:
        speak("Opening Settings")
        subprocess.Popen("ms-settings:", shell=True)

    elif "open paint" in query:
        speak("Opening Paint")
        subprocess.Popen("mspaint.exe")

    elif "take screenshot" in query:
        import pyautogui
        speak("Taking a screenshot")
        pyautogui.screenshot("screenshot.png")
        speak("Screenshot saved!")

    # Web search
    elif "search" in query:
        search_term = query.replace("search", "").strip()
        speak(f"Searching for {search_term}")
        webbrowser.open(f"https://www.google.com/search?q={search_term}")

    # Play music on YouTube
    elif "play" in query:
        song = query.replace("play", "").strip()
        speak(f"Playing {song} on YouTube")
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")

    # Time
    elif "time" in query:
        time = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {time}")

    # Date
    elif "date" in query:
        date = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today's date is {date}")

    # Weather
    elif "weather" in query:
        if "in" in query:
            city = query.split("in")[-1].strip()
        else:
            speak("Which city?")
            city = input("City: ").strip()
        get_weather(city)

    # News
    elif "news" in query or "headlines" in query:
        get_news()
    
    # Notes
    elif "save note" in query or "take note" in query:
        speak("What should I note down?")
        note = input("Note: ").strip()
        save_note(note)

    elif "read notes" in query or "show notes" in query:
        read_notes()

    elif "open notes" in query:
        notes_path = os.path.join(os.path.expanduser("~"), "Documents", "KIRA_Notes.txt")
        speak("Opening your notes!")
        os.startfile(notes_path)

    # Send email
    elif "send email" in query or "send mail" in query:
        speak("Who should I send the email to?")
        to = input("To (email address): ").strip()
        speak("What is the subject?")
        subject = input("Subject: ").strip()
        speak("What should I say in the email?")
        body = input("Message: ").strip()
        send_email(to, subject, body)

    # Exit
    elif any(word in query for word in ["exit", "quit", "bye", "goodbye"]):
        speak("Goodbye! Have a great day!")
        exit()

    # AI brain for everything else
    else:
        speak("Let me think...")
        response = ask_kira(query)
        speak(response)

# Startup
speak("Hello! I am KIRA, your personal AI assistant. How can I help you?")

def listen_for_wake_word():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=3)
            text = r.recognize_google(audio, language="en-in").lower()
            if "kira sync" in text or "kira sink" in text:
                return True
        except:
            pass
    return False

def main():
    speak("Hello! I am KIRA, your personal AI assistant. Say KIRA SYNC to wake me up, or choose an input mode below.")

    while True:
        print("\n[1] Voice  [2] Text  [3] Wake Word Mode  [4] Exit")
        choice = input("Choose input mode: ").strip()

        if choice == "1":
            query = listen()
            handle_command(query)

        elif choice == "2":
            query = input("You: ").strip().lower()
            handle_command(query)

        elif choice == "3":
            speak("Wake word mode activated! Say KIRA SYNC anytime to wake me up.")
            print("Listening for 'KIRA SYNC'... (Press Ctrl+C to exit)")
            while True:
                try:
                    if listen_for_wake_word():
                        speak("Yes? How can I help?")
                        query = listen()
                        handle_command(query)
                except KeyboardInterrupt:
                    speak("Wake word mode deactivated!")
                    break

        elif choice == "4":
            speak("Goodbye!")
            break

main()
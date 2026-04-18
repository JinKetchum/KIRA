from flask import Flask, request, jsonify
import os
import datetime
import webbrowser
import subprocess
import requests as req
from groq import Groq
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
app = Flask(__name__)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

conversation_history = [
    {
        "role": "system",
        "content": "You are KIRA (Kinetic Intelligence & Response Assistant), a helpful, smart and friendly AI assistant. Keep responses concise and clear."
    }
]

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

def get_weather(city):
    try:
        api_key = os.getenv("WEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
        data = req.get(url).json()
        if data["cod"] == 200:
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            description = data["weather"][0]["description"]
            return f"Weather in {city}: {description}. Temp: {temp}°C, feels like {feels_like}°C. Humidity: {humidity}%."
        return "Couldn't find weather for that city."
    except:
        return "Couldn't fetch weather right now."

def get_news():
    try:
        api_key = os.getenv("NEWS_API_KEY")
        url = f"https://newsapi.org/v2/top-headlines?language=en&apiKey={api_key}&pageSize=5"
        data = req.get(url).json()
        articles = data.get("articles", [])
        if articles:
            headlines = "\n".join([f"{i+1}. {a['title']}" for i, a in enumerate(articles)])
            return f"Top Headlines:\n{headlines}"
        return "Couldn't fetch news right now."
    except:
        return "Couldn't fetch news right now."

def save_note(note):
    try:
        notes_path = os.path.join(os.path.expanduser("~"), "Documents", "KIRA_Notes.txt")
        with open(notes_path, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            f.write(f"[{timestamp}] {note}\n")
        return "Note saved successfully!"
    except:
        return "Couldn't save note."

@app.route("/kira", methods=["POST"])
def handle():
    data = request.json
    query = data.get("query", "").lower()
    response = ""

    if "open notepad" in query:
        subprocess.Popen("notepad.exe")
        response = "Opening Notepad!"
    elif "open calculator" in query:
        subprocess.Popen("calc.exe")
        response = "Opening Calculator!"
    elif "open chrome" in query:
        subprocess.Popen("chrome.exe")
        response = "Opening Chrome!"
    elif "open explorer" in query:
        subprocess.Popen("explorer.exe")
        response = "Opening File Explorer!"
    elif "search" in query:
        term = query.replace("search", "").strip()
        webbrowser.open(f"https://www.google.com/search?q={term}")
        response = f"Searching for {term}!"
    elif "play" in query:
        song = query.replace("play", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
        response = f"Playing {song} on YouTube!"
    elif "time" in query:
        response = f"Current time: {datetime.datetime.now().strftime('%I:%M %p')}"
    elif "date" in query:
        response = f"Today: {datetime.datetime.now().strftime('%B %d, %Y')}"
    elif "weather" in query:
        city = query.split("in")[-1].strip() if "in" in query else "Hyderabad"
        response = get_weather(city)
    elif "news" in query or "headlines" in query:
        response = get_news()
    elif "save note" in query or "take note" in query:
        note = query.replace("save note", "").replace("take note", "").strip()
        response = save_note(note) if note else "Please add your note after 'save note'"
    elif "shutdown" in query:
        subprocess.Popen("shutdown /s /t 10", shell=True)
        response = "Shutting down in 10 seconds!"
    elif "lock" in query:
        subprocess.call("rundll32.exe user32.dll,LockWorkStation", shell=True)
        response = "Locking the computer!"
    else:
        response = ask_kira(query)

    return jsonify({"response": response})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "KIRA online!"})

if __name__ == "__main__":
    print("KIRA API running on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
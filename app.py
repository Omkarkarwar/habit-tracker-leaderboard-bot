import os
import requests
import sqlite3
from flask import Flask, request

TOKEN = "7898267747:AAFP-KNJqzCmKzurshWJ0T0xbxhG6zxc164"
API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# Set the webhook for your bot
WEBHOOK_URL = "https://habit-tracker-leaderboard-bot.onrender.com"  # Correct URL
webhook_set_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
response = requests.get(webhook_set_url)

# Check if setting the webhook was successful
if response.status_code == 200:
    print("Webhook set successfully!")
else:
    print("Failed to set webhook")

# Function to send a message
def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# Function to send a message
def send_message(chat_id, text):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

# Function to connect to the database
def connect_db():
    conn = sqlite3.connect("habits.db", check_same_thread=False)
    cursor = conn.cursor()
    return conn, cursor

# Function to initialize database and create tables
def init_db():
    conn, cursor = connect_db()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS habits (
        user_id INTEGER,
        habit_name TEXT,
        streak INTEGER DEFAULT 0,
        last_updated DATE,
        PRIMARY KEY (user_id, habit_name)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS leaderboard (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        total_streak INTEGER DEFAULT 0
    )
    ''')
    conn.commit()
    conn.close()

# Call init_db function when the app starts
init_db()

# Webhook route to handle Telegram messages
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "").strip()
        
        if text == "/start":
            send_message(chat_id, "Welcome to your Habit Tracker Bot! 🏆\nType /help to see available commands.")
        
        elif text == "/help":
            send_message(chat_id, "Commands:\n/addhabit habit_name - Add a new habit\n/listhabits - View all habits\n/done habit_name - Mark habit as done\n/streaks - View your habit streaks\n/leaderboard - View top users")
        
        elif text.startswith("/addhabit"):
            habit_name = text[10:].strip()
            if habit_name:
                conn, cursor = connect_db()
                cursor.execute("INSERT INTO habits (user_id, habit_name, streak, last_updated) VALUES (?, ?, 0, DATE('now'))", (chat_id, habit_name))
                conn.commit()
                conn.close()
                send_message(chat_id, f"✅ Habit '{habit_name}' added successfully!")
            else:
                send_message(chat_id, "❌ Please provide a habit name. Example: /addhabit running")
        
        elif text == "/listhabits":
            conn, cursor = connect_db()
            cursor.execute("SELECT habit_name FROM habits WHERE user_id=?", (chat_id,))
            habits = cursor.fetchall()
            conn.close()
            if habits:
                habit_list = "\n".join([f"- {habit[0]}" for habit in habits])
                send_message(chat_id, f"📋 Your Habits:\n{habit_list}")
            else:
                send_message(chat_id, "❌ You have no habits yet. Add one using /addhabit habit_name")
        
        elif text.startswith("/done"):
            habit_name = text[6:].strip()
            if not habit_name:
                send_message(chat_id, "❌ Please provide a habit name. Example: /done running")
            else:
                conn, cursor = connect_db()
                cursor.execute("UPDATE habits SET streak = streak + 1, last_updated = DATE('now') WHERE user_id=? AND habit_name=?", (chat_id, habit_name))
                
                # Check if user exists in leaderboard
                cursor.execute("SELECT total_streak FROM leaderboard WHERE user_id=?", (chat_id,))
                user = cursor.fetchone()
                
                if user:
                    cursor.execute("UPDATE leaderboard SET total_streak = total_streak + 1 WHERE user_id=?", (chat_id,))
                else:
                    cursor.execute("INSERT INTO leaderboard (user_id, username, total_streak) VALUES (?, ?, 1)", (chat_id, f"User-{chat_id}"))
                
                conn.commit()
                conn.close()
                send_message(chat_id, f"✅ Habit '{habit_name}' marked as completed! 🎯")
        
        elif text == "/leaderboard":
            conn, cursor = connect_db()
            cursor.execute("SELECT username, total_streak FROM leaderboard ORDER BY total_streak DESC LIMIT 10")
            top_users = cursor.fetchall()
            conn.close()
            
            if top_users:
                leaderboard_text = "🏆 *Leaderboard* 🏆\n"
                for rank, (username, total_streak) in enumerate(top_users, 1):
                    leaderboard_text += f"{rank}. {username} - {total_streak} streaks 🔥\n"
                send_message(chat_id, leaderboard_text)
            else:
                send_message(chat_id, "❌ No leaderboard data available yet.")
    
    return "OK", 200

# Running the app
if __name__ == "__main__":
    app.run(debug=True)

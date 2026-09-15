import requests
import time
import schedule
import random
import datetime
import os
import threading
from flask import Flask

# === CONFIGURATION ===
FIREBASE_URL = "https://movie-ee8bb-default-rtdb.firebaseio.com"
TG_BOT_TOKEN = "8937841235:AAGXAhKUEay2uYUIcaXCA560MvrayUhPHIQ"
TG_CHANNEL = "@goearninfo"
HF_API_URL = "https://stsgsvcsg-abtxy.hf.space/call/img"

def daily_task():
    print(f"[{datetime.datetime.now()}] Starting daily bot task...")
    
    # 1. DELETE OLD CODE
    try:
        last_code_res = requests.get(f"{FIREBASE_URL}/settings/last_bot_code.json")
        if last_code_res.status_code == 200 and last_code_res.json():
            last_code = last_code_res.json().get('code')
            if last_code:
                requests.delete(f"{FIREBASE_URL}/redeem_codes/{last_code}.json")
                print(f"Deleted old code: {last_code}")
    except Exception as e:
        print(f"Error deleting old code: {e}")

    # 2. CREATE NEW CODE & DETERMINE PRICE
    today = datetime.datetime.today().weekday()
    reward = 3 if today == 0 else random.randint(1, 2)
    new_code = f"GOEARN{random.randint(1000, 9999)}"
    
    code_data = {
        "amount": reward,
        "maxUses": 100,
        "usedCount": 0,
        "usedBy": []
    }
    
    requests.put(f"{FIREBASE_URL}/redeem_codes/{new_code}.json", json=code_data)
    requests.put(f"{FIREBASE_URL}/settings/last_bot_code.json", json={"code": new_code})
    print(f"Generated new code: {new_code} for ₹{reward}")

    # 3. GENERATE AI IMAGE
    prompts = [
        "A glowing magical treasure chest full of gold coins, 3d render, cinematic lighting",
        "A futuristic cyberpunk gift box with neon lights, highly detailed, 4k",
        "A beautiful diamond floating with money around it, vibrant colors, masterpiece",
        "A golden ticket glowing in the dark, magical atmosphere, ultra realistic"
    ]
    selected_prompt = random.choice(prompts)
    
    image_url = "https://i.ibb.co/hxY1Vpyw/IMG-20260816-122032-675.jpg"
    try:
        print("Generating AI Image...")
        hf_res = requests.post(HF_API_URL, json={"data": [selected_prompt]}, timeout=60)
        hf_data = hf_res.json()
        if "data" in hf_data and hf_data["data"]:
            if isinstance(hf_data["data"][0], dict) and "url" in hf_data["data"][0]:
                image_url = hf_data["data"][0]["url"]
            elif isinstance(hf_data["data"][0], str):
                image_url = hf_data["data"][0]
        print(f"Image generated successfully: {image_url}")
    except Exception as e:
        print(f"AI Image generation failed, using fallback. Error: {e}")

    # 4. SEND TO TELEGRAM
    caption = (
        "🎁 *DAILY MEGA REDEEM CODE* 🎁\n\n"
        f"🎟 *Code:* `{new_code}`\n"
        f"💸 *Amount:* ₹{reward}\n"
        "👥 *Limit:* First 100 Users\n\n"
        "🚀 *App me jao aur turant claim karo!*"
    )
    
    tg_api = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    tg_payload = {
        "chat_id": TG_CHANNEL,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    
    try:
        requests.post(tg_api, data=tg_payload)
        print("Message sent to Telegram successfully!")
    except Exception as e:
        print(f"Failed to send to Telegram: {e}")

    print("Task completed!\n")

# === BACKGROUND SCHEDULER THREAD ===
def run_bot():
    print("Background Bot Thread Started...")
    daily_task() # Run once on startup
    schedule.every().day.at("04:30").do(daily_task) # 04:30 UTC = 10:00 AM IST
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# === DUMMY WEB SERVER FOR RENDER ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Go Earn Bot is running perfectly in the background!"

if __name__ == "__main__":
    # Start the bot in a separate background thread
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Start the web server to satisfy Render's port requirement
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

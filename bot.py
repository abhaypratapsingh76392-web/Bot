import requests
import time
import schedule
import random
import datetime
import os
import threading
from flask import Flask
from gradio_client import Client

# === CONFIGURATION ===
FIREBASE_URL = "https://movie-ee8bb-default-rtdb.firebaseio.com"
TG_BOT_TOKEN = "8937841235:AAGXAhKUEay2uYUIcaXCA560MvrayUhPHIQ"
TG_CHANNEL = "@goearninfo"
HF_SPACE_URL = "https://stsgsvcsg-abtxy.hf.space"

def daily_task():
    print(f"[{datetime.datetime.now()}] Starting daily bot task...")
    
    # 1. DELETE OLD CODE (Bot wala)
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
    new_code = f"GOEARN{random.randint(100, 999)}" # Thoda chhota code taaki AI achhe se text likh sake
    
    code_data = {
        "amount": reward,
        "maxUses": 100,
        "usedCount": 0,
        "usedBy": []
    }
    
    # Save to Firebase
    requests.put(f"{FIREBASE_URL}/redeem_codes/{new_code}.json", json=code_data)
    requests.put(f"{FIREBASE_URL}/settings/last_bot_code.json", json={"code": new_code})
    print(f"Generated new code: {new_code} for ₹{reward}")

    # 3. GENERATE AI IMAGE WITH CODE TEXT (Using Gradio Client exactly like HTML)
    # Prompt mein hum explicitly bol rahe hain ki image par code likho
    best_prompt = f"A high quality 3D render of a futuristic cyberpunk glowing neon sign displaying the text '{new_code}', cinematic lighting, dark background, 8k resolution, masterpiece"
    
    image_path = None
    fallback_image = "https://i.ibb.co/hxY1Vpyw/IMG-20260816-122032-675.jpg"

    try:
        print(f"Connecting to AI Space for text image: {new_code}...")
        client = Client(HF_SPACE_URL)
        result = client.predict(prompt=best_prompt, api_name="/img")
        
        # Gradio client image ko local file mein save karta hai aur path return karta hai
        image_path = result
        print(f"AI Image generated successfully at: {image_path}")
    except Exception as e:
        print(f"AI Image generation failed: {e}. Using fallback image.")

    # 4. SEND TO TELEGRAM
    caption = (
        "🎁 *DAILY MEGA REDEEM CODE* 🎁\n\n"
        f"🎟 *Code:* `{new_code}`\n"
        f"💸 *Amount:* ₹{reward}\n"
        "👥 *Limit:* First 100 Users\n\n"
        "🚀 *App me jao aur turant claim karo!*"
    )
    
    tg_api_photo = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendPhoto"
    
    try:
        if image_path and os.path.exists(image_path):
            # Agar AI image bani hai toh file upload karo
            with open(image_path, 'rb') as photo_file:
                payload = {"chat_id": TG_CHANNEL, "caption": caption, "parse_mode": "Markdown"}
                files = {"photo": photo_file}
                requests.post(tg_api_photo, data=payload, files=files)
        else:
            # Agar AI fail ho gaya toh default image URL bhejo
            payload = {"chat_id": TG_CHANNEL, "photo": fallback_image, "caption": caption, "parse_mode": "Markdown"}
            requests.post(tg_api_photo, data=payload)
            
        print("Message sent to Telegram successfully!")
    except Exception as e:
        print(f"Failed to send to Telegram: {e}")

    print("Task completed!\n")

# === BACKGROUND SCHEDULER THREAD ===
def run_bot():
    print("Background Bot Thread Started...")
    daily_task() # Start hote hi ek baar run karega test ke liye
    schedule.every().day.at("04:30").do(daily_task) # Roz chalega
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# === DUMMY WEB SERVER FOR RENDER ===
app = Flask(__name__)

@app.route('/')
def home():
    return "🚀 Go Earn Auto-Bot with AI Image Text is running perfectly!"

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

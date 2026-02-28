import os
import asyncio
from telegram import Bot
from dotenv import load_dotenv

async def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("No token found in .env")
        return
    
    try:
        bot = Bot(token)
        me = await bot.get_me()
        print(f"CONFIRMED BOT IDENTITY:")
        print(f"Name: {me.first_name}")
        print(f"Username: @{me.username}")
        print("-" * 30)
        print("INSTRUCTIONS FOR USER:")
        print(f"1. Open Telegram and search for @{me.username}")
        print("2. If you don't see a 'START' button, just type /start manually.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

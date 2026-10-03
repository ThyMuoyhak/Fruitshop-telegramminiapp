"""
bot_worker.py - Entry point for Render deployment.
Supports running both as a Web Service (FastAPI + Bot) or as a standalone Bot Worker.
"""
import os
import sys

# Ensure UTF-8 output on Windows or Linux console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import run_all
import bot

def main():
    # If PORT is provided (Render Web Service), run both Web Server and Telegram Bot
    if os.getenv("PORT") or os.getenv("SERVER_PORT"):
        print("🌐 [Worker] PORT detected. Launching Unified Platform (FastAPI Web + Telegram Bot)...")
        run_all.main()
    else:
        # Otherwise run standalone bot worker
        print("🤖 [Worker] No PORT detected. Launching Telegram Bot...")
        bot.main()

if __name__ == "__main__":
    main()

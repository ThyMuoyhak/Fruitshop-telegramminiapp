import sys
import multiprocessing
import uvicorn
import time

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import config
import database
import bot

def start_web_server():
    print(f"🚀 [Web Server] Starting FastAPI on {config.SERVER_HOST}:{config.SERVER_PORT}...")
    uvicorn.run("server:app", host=config.SERVER_HOST, port=config.SERVER_PORT, log_level="info")

def main():
    print("=" * 60)
    print(f"🍎 FOOD FRUIT KH — UNIFIED PLATFORM")
    print(f"🛍️ Telegram MiniApp: {config.WEBAPP_URL}")
    print(f"⚙️ Admin Dashboard: http://localhost:{config.SERVER_PORT}/admin")
    print(f"🤖 Telegram Bot: @{config.BOT_USERNAME}")
    print("=" * 60)

    # Initialize database
    database.init_db()

    # Start FastAPI server in background process
    server_process = multiprocessing.Process(target=start_web_server)
    server_process.daemon = True
    server_process.start()

    time.sleep(1.5)

    # Start Telegram Bot in main thread
    try:
        bot.main()
    except (KeyboardInterrupt, SystemExit):
        print("\nStopping services...")
    finally:
        if server_process.is_alive():
            server_process.terminate()

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

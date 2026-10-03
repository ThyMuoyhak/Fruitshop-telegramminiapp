"""
Unified Background Worker for backend/
Runs FastAPI REST API on the assigned $PORT while running the Telegram Bot asynchronously in the same process.
"""
import asyncio
import os
import uvicorn
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("worker")

async def run_fastapi(port: int):
    from main import app
    config_server = uvicorn.Config(app=app, host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config_server)
    logger.info(f"Starting FastAPI REST API on port {port}...")
    await server.serve()

async def run_telegram_bot():
    from bot import start_bot_coroutine
    logger.info("Starting Telegram Bot Engine...")
    await start_bot_coroutine()

async def main():
    port = int(os.environ.get("PORT", 8000))
    await asyncio.gather(
        run_fastapi(port),
        run_telegram_bot()
    )

if __name__ == "__main__":
    asyncio.run(main())

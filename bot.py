import sys
import os
import logging
import asyncio
import warnings

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from telegram.warnings import PTBUserWarning
warnings.filterwarnings("ignore", category=PTBUserWarning)

from telegram import Update, BotCommand, MenuButtonWebApp, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

import config
import database
import keyboards
from handlers import start, catalog, cart, checkout, orders, admin

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    """
    Sets up bot commands, database, and Telegram WebApp Chat Menu Button on start.
    """
    database.init_db()
    
    # Keep only 1 command for Open Shop as requested
    commands = [
        BotCommand("shop", "🛍️ បើកហាងទំនិញ / Open Shop")
    ]
    await application.bot.set_my_commands(commands)

    # Set Persistent Telegram Chat Menu Button to MiniApp
    if config.WEBAPP_URL.startswith("https://"):
        try:
            await application.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(text="🛍️ Open Shop", web_app=WebAppInfo(url=config.WEBAPP_URL))
            )
            logger.info(f"Telegram Chat Menu Button set to MiniApp URL: {config.WEBAPP_URL}")
        except Exception as e:
            logger.warning(f"Could not configure Chat Menu Button: {e}")
    else:
        logger.info(f"Local HTTP mode: MiniApp running at {config.WEBAPP_URL}. Set HTTPS domain/tunnel to activate native chat menu button.")

    logger.info(f"Bot @{config.BOT_USERNAME} initialized successfully with DB and commands.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """
    Global error handler for unhandled exceptions.
    """
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ មានបញ្ហាបច្ចេកទេសមួយបានកើតឡើង។ សូមសាកល្បងម្ដងទៀត ឬទាក់ទងមកកាន់ @thymuoyhak ។"
            )
        except Exception:
            pass

def build_bot_app():
    # Initialize SQLite database
    database.init_db()

    app = ApplicationBuilder().token(config.BOT_TOKEN).post_init(post_init).build()

    # 1. Conversation Handlers (High Priority)
    app.add_handler(checkout.get_checkout_handler())
    app.add_handler(admin.get_broadcast_handler())

    # 2. Command Handlers
    app.add_handler(CommandHandler("start", start.start_command))
    app.add_handler(CommandHandler("shop", start.open_shop_message))
    app.add_handler(CommandHandler("help", start.help_command))
    app.add_handler(CommandHandler("store", catalog.store_menu))
    app.add_handler(CommandHandler("cart", cart.view_cart))
    app.add_handler(CommandHandler("orders", orders.my_orders_menu))
    app.add_handler(CommandHandler("profile", start.profile_command))
    app.add_handler(CommandHandler("admin", admin.admin_dashboard))

    # 3. Text & Menu Handlers (Persistent Reply Keyboard)
    app.add_handler(MessageHandler(filters.Regex(r"(?i)(បើកហាង|open\s*shop)"), start.open_shop_message))
    app.add_handler(MessageHandler(filters.Regex("(?i)(ទិញទំនិញ|store)"), catalog.store_menu))
    app.add_handler(MessageHandler(filters.Regex("(?i)(កន្ត្រក|cart)"), cart.view_cart))
    app.add_handler(MessageHandler(filters.Regex("(?i)(ប្រវត្តិ|orders)"), orders.my_orders_menu))
    app.add_handler(MessageHandler(filters.Regex("(?i)(គណនី|profile)"), start.profile_command))
    app.add_handler(MessageHandler(filters.Regex("(?i)(ជំនួយ|help|support)"), start.help_command))
    app.add_handler(MessageHandler(filters.Regex("(?i)(admin|dashboard)"), admin.admin_dashboard))

    # 4. Callback Query Handlers (Inline Buttons)
    # General & Nav
    app.add_handler(CallbackQueryHandler(start.open_shop_callback, pattern="^open_shop_link$"))
    app.add_handler(CallbackQueryHandler(start.home_menu_callback, pattern="^menu_home$"))
    app.add_handler(CallbackQueryHandler(start.help_command, pattern="^help_menu$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern="^ignore$"))

    # Catalog & Products
    app.add_handler(CallbackQueryHandler(catalog.store_menu, pattern="^all_categories$"))
    app.add_handler(CallbackQueryHandler(catalog.category_detail, pattern="^cat_\\d+$"))
    app.add_handler(CallbackQueryHandler(catalog.product_detail, pattern="^prod_\\d+$"))
    app.add_handler(CallbackQueryHandler(catalog.adjust_quantity, pattern="^qty_(plus|minus)_\\d+_\\d+$"))
    app.add_handler(CallbackQueryHandler(catalog.add_to_cart_handler, pattern="^add_cart_\\d+_\\d+$"))

    # Cart
    app.add_handler(CallbackQueryHandler(cart.view_cart, pattern="^view_cart$"))
    app.add_handler(CallbackQueryHandler(cart.cart_action, pattern="^cart_(inc|dec|del)_\\d+$"))
    app.add_handler(CallbackQueryHandler(cart.cart_clear_handler, pattern="^cart_clear$"))

    # Orders & Payments
    app.add_handler(CallbackQueryHandler(orders.my_orders_menu, pattern="^my_orders$"))
    app.add_handler(CallbackQueryHandler(orders.view_order_detail, pattern="^view_order_.*$"))
    app.add_handler(CallbackQueryHandler(orders.verify_payment_callback, pattern="^verify_pay_.*$"))
    app.add_handler(CallbackQueryHandler(orders.show_qr_callback, pattern="^show_qr_.*$"))
    app.add_handler(CallbackQueryHandler(orders.cancel_order_callback, pattern="^cancel_order_.*$"))

    # Admin Panel Callbacks
    app.add_handler(CallbackQueryHandler(admin.admin_dashboard, pattern="^admin_home$"))
    app.add_handler(CallbackQueryHandler(admin.admin_dashboard, pattern="^admin_stats$"))
    app.add_handler(CallbackQueryHandler(admin.admin_orders_menu, pattern="^admin_orders_menu$"))
    app.add_handler(CallbackQueryHandler(admin.admin_list_orders, pattern="^admin_list_orders_.*$"))
    app.add_handler(CallbackQueryHandler(admin.admin_view_single_order, pattern="^adm_view_order_.*$"))
    app.add_handler(CallbackQueryHandler(admin.admin_set_order_status, pattern="^adm_set_.*$"))
    app.add_handler(CallbackQueryHandler(admin.admin_products_menu, pattern="^admin_products$"))
    app.add_handler(CallbackQueryHandler(admin.admin_toggle_product, pattern="^adm_toggle_prod_\\d+$"))

    # 5. Error Handler
    app.add_error_handler(error_handler)
    return app

async def start_bot_coroutine():
    """
    Asynchronous runner for integration inside bot_worker.py with FastAPI.
    """
    logger.info("Initializing Telegram Bot in background worker mode...")
    app = build_bot_app()
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    logger.info(f"Telegram Bot @{config.BOT_USERNAME} polling started successfully in background.")
    try:
        while True:
            await asyncio.sleep(3600)
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()

def main():
    print(f"==================================================")
    print(f"🚀 Starting {config.STORE_NAME_EN} Telegram Bot...")
    print(f"🤖 Bot Username: @{config.BOT_USERNAME}")
    print(f"👤 Admin IDs: {config.ADMIN_IDS}")
    print(f"💳 Payment Gateway: AnajakPay KHQRcc (ABA Pay)")
    print(f"==================================================")

    app = build_bot_app()
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

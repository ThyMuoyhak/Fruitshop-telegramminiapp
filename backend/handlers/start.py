import logging
from telegram import Update
from telegram.ext import ContextTypes

import config
import database
import keyboards

logger = logging.getLogger(__name__)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    database.register_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "",
        last_name=user.last_name or ""
    )

    is_admin = user.id in config.ADMIN_IDS

    welcome_text = (
        f"👋 <b>សួស្តី {user.first_name}! សូមស្វាគមន៍មកកាន់ {config.STORE_NAME_KH}!</b>\n"
        f"🍍 <i>Welcome to {config.STORE_NAME_EN} Telegram Store!</i>\n\n"
        f"យើងខ្ញុំមានលក់ផ្លែឈើស្រស់ៗធម្មជាតិពីគ្រប់ខេត្ត ផ្លែឈើក្រៀម ទឹកផ្លែឈើស្រស់ "
        f"និងអាហារសម្រន់ខ្មែរឆ្ងាញ់ៗជាច្រើនមុខ ជាមួយការដឹកជញ្ជូនរហ័សទាន់ចិត្ត!\n\n"
        f"💳 <b>ការទូទាត់ប្រាក់ងាយស្រួល:</b> គាំទ្រ <b>KHQR / ABA Pay</b> ស្កេនទូទាត់រហ័សទាន់ចិត្តតាមទូរស័ព្ទដៃ。\n\n"
        f"👇 <b>សូមចុចប៊ូតុង '🛍️ Open Shop' ខាងក្រោមដើម្បីបើកហាងទំនិញ៖</b>"
    )

    reply_markup = keyboards.get_main_menu_keyboard(is_admin=is_admin)
    await update.message.reply_html(welcome_text, reply_markup=reply_markup)

async def open_shop_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"🛍️ <b>សូមចុចលើតំណភ្ជាប់ខាងក្រោមដើម្បីបើកហាងទំនិញ (Open Shop):</b>\n\n"
        f"👉 <b><a href=\"{config.WEBAPP_URL}\">{config.WEBAPP_URL}</a></b>\n\n"
        f"💡 <i>(ចុចលើ Link ខាងលើដើម្បីបើកមើលទំនិញ និងកុម្ម៉ង់ទិញបានភ្លាមៗ!)</i>"
    )
    inline_markup = keyboards.get_miniapp_welcome_keyboard()
    await update.message.reply_html(msg, reply_markup=inline_markup)

async def open_shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    msg = (
        f"🛍️ <b>សូមចុចលើតំណភ្ជាប់ខាងក្រោមដើម្បីបើកហាងទំនិញ (Open Shop):</b>\n\n"
        f"👉 <b><a href=\"{config.WEBAPP_URL}\">{config.WEBAPP_URL}</a></b>\n\n"
        f"💡 <i>(ចុចលើ Link ខាងលើដើម្បីបើកមើលទំនិញ និងកុម្ម៉ង់ទិញបានភ្លាមៗ!)</i>"
    )
    await query.message.reply_html(msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"ℹ️ <b>មជ្ឈមណ្ឌលជំនួយ & ទំនាក់ទំនង / Help & Support</b>\n\n"
        f"🏪 <b>ហាង:</b> {config.STORE_NAME_KH} ({config.STORE_NAME_EN})\n"
        f"📞 <b>លេខទូរស័ព្ទ / Phone:</b> {config.SUPPORT_PHONE}\n"
        f"💬 <b>Telegram ផ្ទាល់:</b> @{config.STORE_CONTACT_USERNAME}\n"
        f"🕒 <b>ម៉ោងបម្រើការ / Hours:</b> 7:30 AM - 9:00 PM (រៀងរាល់ថ្ងៃ)\n"
        f"📍 <b>តំបន់សេវាកម្ម:</b> រាជធានីភ្នំពេញ & បញ្ញើទៅបណ្តាខេត្ត\n\n"
        f"💡 <b>របៀបបញ្ជាទិញ (How to order):</b>\n"
        f"1. ចុច '🍎 ទិញទំនិញ / Store' ដើម្បីមើលមុខទំនិញ\n"
        f"2. ជ្រើសរើសចំនួន ហើយចុច '🛒 បញ្ចូលទៅកន្ត្រក'\n"
        f"3. ចូលទៅកាន់ '🛒 កន្ត្រក' រួចចុច Checkout\n"
        f"4. បំពេញព័ត៌មានដឹកជញ្ជូន និងស្កេន KHQR តាម ABA Mobile\n"
        f"5. ប្រព័ន្ធនឹងផ្ទៀងផ្ទាត់ការបង់ប្រាក់ដោយស្វ័យប្រវត្តិភ្លាមៗ!"
    )
    if update.message:
        await update.message.reply_html(help_text)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(help_text, parse_mode="HTML")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_user = database.get_user(user.id) or {}
    orders = database.get_user_orders(user.id, limit=5)

    profile_text = (
        f"👤 <b>ព័ត៌មានគណនីរបស់អ្នក / Your Profile</b>\n\n"
        f"🆔 <b>Telegram ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>ឈ្មោះ / Name:</b> {user.full_name}\n"
        f"🔗 <b>Username:</b> @{user.username if user.username else 'N/A'}\n"
        f"📱 <b>លេខទូរស័ព្ទ / Phone:</b> {db_user.get('phone') or 'មិនទាន់កំណត់ (Not set)'}\n"
        f"📍 <b>អាសយដ្ឋានចុងក្រោយ:</b> {db_user.get('address') or 'មិនទាន់កំណត់ (Not set)'}\n\n"
        f"📦 <b>ចំនួនការបញ្ជាទិញសរុប:</b> {len(orders)} ដង\n"
    )

    await update.message.reply_html(profile_text)

async def home_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    is_admin = user.id in config.ADMIN_IDS

    welcome_text = (
        f"🏠 <b>មឺនុយដើម / Main Menu - {config.STORE_NAME_KH}</b>\n\n"
        f"សូមជ្រើសរើសផ្នែកខាងក្រោមដើម្បីបន្តការទិញទំនិញស្រស់ៗ៖"
    )
    categories = database.get_categories()
    await query.edit_message_text(
        welcome_text,
        reply_markup=keyboards.get_categories_keyboard(categories),
        parse_mode="HTML"
    )

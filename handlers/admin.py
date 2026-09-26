import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters

import config
import database
import keyboards

logger = logging.getLogger(__name__)

# State for broadcast conversation
ADMIN_BROADCAST_STATE = 1

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main Admin Dashboard showing KPIs and management tools.
    """
    user = update.effective_user
    if not is_admin(user.id):
        if update.message:
            await update.message.reply_text("⛔ អ្នកមិនមានសិទ្ធិចូលប្រើប្រាស់ផ្ទាំងនេះទេ! (Admin Only)")
        return

    stats = database.get_sales_stats()
    text = (
        f"⚙️ <b>ផ្ទាំងគ្រប់គ្រងអ្នកគ្រប់គ្រង / Admin Dashboard</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏪 <b>ហាង:</b> {config.STORE_NAME_KH} ({config.STORE_NAME_EN})\n"
        f"👤 <b>Admin:</b> {user.full_name} (<code>{user.id}</code>)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>ស្ថិតិអាជីវកម្មសង្ខេប / Summary KPIs:</b>\n"
        f"👥 <b>អតិថិជនសរុប (Users):</b> <b>{stats['total_users']}</b> នាក់\n"
        f"📦 <b>ការកុម្ម៉ង់សរុប (Total Orders):</b> <b>{stats['total_orders']}</b>\n"
        f"💰 <b>ចំណូលសរុប (Total Revenue):</b> <b>${stats['total_revenue']:.2f} USD</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"✅ <b>បានបង់ប្រាក់ (Paid Orders):</b> <b>{stats['paid_orders']}</b> (${stats['paid_revenue']:.2f})\n"
        f"⏳ <b>រង់ចាំបង់ប្រាក់ (Pending):</b> <b>{stats['pending_orders']}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>សូមជ្រើសរើសផ្នែកខាងក្រោមដើម្បីគ្រប់គ្រង៖</i>"
    )

    reply_markup = keyboards.get_admin_dashboard_keyboard()

    if update.message:
        await update.message.reply_html(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def admin_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Filter menu for orders.
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    await query.answer()
    text = "📦 <b>គ្រប់គ្រងការបញ្ជាទិញ / Manage Orders</b>\n\nសូមជ្រើសរើសស្ថានភាពដែលចង់មើល៖"
    reply_markup = keyboards.get_admin_orders_filter_keyboard()
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def admin_list_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lists orders according to selected filter.
    Callback data: admin_list_orders_<STATUS>
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    await query.answer()
    status_filter = query.data.replace("admin_list_orders_", "")

    if status_filter == "ALL":
        orders = database.get_all_orders(limit=25)
        title = "ការកុម្ម៉ង់ទាំងអស់ (All Orders)"
    else:
        orders = database.get_all_orders(status_filter=status_filter, limit=25)
        title = f"ការកុម្ម៉ង់ស្ថានភាព: {status_filter}"

    if not orders:
        text = f"📦 <b>{title}</b>\n\nមិនមានទិន្នន័យនៅក្នុងបញ្ជីនេះទេ (No orders found)."
        btn = [[InlineKeyboardButton("⬅️ Back to Filter", callback_data="admin_orders_menu")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(btn), parse_mode="HTML")
        return

    text = f"📦 <b>{title} (សរុប {len(orders)}):</b>\n\nចុចលើការកុម្ម៉ង់ដើម្បីមើលលម្អិត ឬប្តូរស្ថានភាព៖"
    buttons = []
    for o in orders:
        btn_text = f"#{o['order_id']} | ${o['total_amount']:.2f} - {o['delivery_name']} ({o['status']})"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"adm_view_order_{o['transaction_id']}")])

    buttons.append([InlineKeyboardButton("⬅️ Back to Orders Menu", callback_data="admin_orders_menu")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

async def admin_view_single_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin detailed view for an order with management buttons.
    Callback data: adm_view_order_<tx_id>
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    await query.answer()
    tx_id = query.data.replace("adm_view_order_", "")
    order = database.get_order_by_tx(tx_id)

    if not order:
        await query.answer("រកមិនឃើញ Order នេះទេ!", show_alert=True)
        return

    text_lines = [
        f"⚙️ <b>គ្រប់គ្រងការកុម្ម៉ង់ / Manage Order #{order['order_id']}</b>",
        f"━━━━━━━━━━━━━━━━━━",
        f"🔖 <b>Transaction ID:</b> <code>{order['transaction_id']}</code>",
        f"🚦 <b>ស្ថានភាពបច្ចុប្បន្ន:</b> <b>{order['status']}</b>",
        f"📅 <b>កាលបរិច្ឆេទ:</b> {order['created_at'][:19].replace('T', ' ')}",
        f"━━━━━━━━━━━━━━━━━━",
        f"👤 <b>អតិថិជន:</b> {order['delivery_name']} (User ID: <code>{order['user_id']}</code>)",
        f"📱 <b>លេខទូរស័ព្ទ:</b> <code>{order['delivery_phone']}</code>",
        f"📍 <b>អាសយដ្ឋានដឹក:</b> {order['delivery_address']}",
        f"📝 <b>ចំណាំ:</b> {order.get('delivery_note') or 'គ្មាន'}",
        f"━━━━━━━━━━━━━━━━━━",
        f"🛒 <b>មុខទំនិញ:</b>"
    ]
    for item in order.get("items", []):
        text_lines.append(f" • {item['product_name']} x {item['quantity']} ({item['unit']}) = ${item['subtotal']:.2f}")

    text_lines.append(f"━━━━━━━━━━━━━━━━━━")
    text_lines.append(f"💰 <b>ទឹកប្រាក់សរុប:</b> <b>${order['total_amount']:.2f} USD</b>")
    if order.get("paid_at"):
        text_lines.append(f"✅ <b>ទូទាត់នៅម៉ោង:</b> {order['paid_at'][:19].replace('T', ' ')}")

    reply_markup = keyboards.get_admin_order_manage_keyboard(order["order_id"], tx_id, order["status"])
    await query.edit_message_text("\n".join(text_lines), reply_markup=reply_markup, parse_mode="HTML")

async def admin_set_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin updates status of order (PROCESSING, DELIVERING, COMPLETED, CANCELLED).
    Callback data: adm_set_<tx_id>_<NEW_STATUS>
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    parts = query.data.split("_")
    # adm_set_<tx_id>_<NEW_STATUS>
    new_status = parts[-1]
    tx_id = "_".join(parts[2:-1])

    order = database.get_order_by_tx(tx_id)
    if not order:
        await query.answer("រកមិនឃើញ Order នេះទេ!", show_alert=True)
        return

    database.update_order_status(tx_id, new_status)
    await query.answer(f"✅ បានប្តូរស្ថានភាពទៅជា: {new_status}!", show_alert=True)

    # Customer notifications mapping
    status_customer_notifs = {
        "PROCESSING": (
            f"👨‍🍳 <b>ការកុម្ម៉ង់ #{order['order_id']} កំពុងត្រូវបានរៀបចំ!</b>\n\n"
            f"ហាងកំពុងជ្រើសរើសផ្លែឈើស្រស់ៗ និងវេចខ្ចប់យ៉ាងស្អាតជូនលោកអ្នក។ យើងខ្ញុំនឹងជូនដំណឹងបន្តនៅពេលដឹកជញ្ជូនចេញ!"
        ),
        "DELIVERING": (
            f"🛵 <b>ការកុម្ម៉ង់ #{order['order_id']} កំពុងត្រូវបានដឹកជញ្ជូន!</b>\n\n"
            f"អ្នកដឹកជញ្ជូនកំពុងធ្វើដំណើរទៅកាន់អាសយដ្ឋាន៖ {order['delivery_address']}\n"
            f"សូមត្រៀមទទួលទូរស័ព្ទពីអ្នកដឹកជញ្ជូនតាមលេខ៖ {order['delivery_phone']}។"
        ),
        "COMPLETED": (
            f"🎉 <b>ការកុម្ម៉ង់ #{order['order_id']} បានដឹកជញ្ជូនដល់ជោគជ័យ!</b>\n\n"
            f"សូមអរគុណយ៉ាងជ្រាលជ្រៅសម្រាប់ការគាំទ្រហាង {config.STORE_NAME_KH}! សង្ឃឹមថាលោកអ្នកនឹងពេញចិត្តជាមួយរសជាតិផ្លែឈើ និងអាហាររបស់យើងខ្ញុំ។"
        ),
        "CANCELLED": (
            f"❌ <b>ការកុម្ម៉ង់ #{order['order_id']} ត្រូវបានបោះបង់ដោយហាង។</b>\n\n"
            f"ប្រសិនបើមានចម្ងល់ សូមទាក់ទងមកកាន់ @{config.STORE_CONTACT_USERNAME}។"
        )
    }

    if new_status in status_customer_notifs:
        try:
            await context.application.bot.send_message(
                chat_id=order["user_id"],
                text=status_customer_notifs[new_status],
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Could not notify customer about status change: {e}")

    # Refresh admin view
    await admin_view_single_order(update, context)

# --- Manage Products & Stock ---

async def admin_products_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Product stock management.
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    await query.answer()
    products = database.get_all_products()

    text = (
        f"🍎 <b>គ្រប់គ្រងទំនិញក្នុងស្តុក / Manage Products & Stock</b>\n\n"
        f"ចុចលើទំនិញណាមួយដើម្បី <b>បិទ/បើកស្តុក (Toggle In Stock / Out of Stock)</b>៖\n"
        f"✅ = មានក្នុងស្តុក (In Stock) | ❌ = ដាច់ស្តុក (Out of Stock)"
    )

    buttons = []
    for p in products:
        icon = "✅" if p["is_available"] else "❌"
        btn_text = f"{icon} {p['name_kh']} (${p['price']:.2f})"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"adm_toggle_prod_{p['id']}")])

    buttons.append([InlineKeyboardButton("⬅️ Back to Admin Dashboard", callback_data="admin_home")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="HTML")

async def admin_toggle_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Toggles product availability.
    Callback data: adm_toggle_prod_<id>
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    prod_id = int(query.data.replace("adm_toggle_prod_", ""))
    database.toggle_product_availability(prod_id)
    await query.answer("🔄 បានផ្លាស់ប្តូរស្ថានភាពស្តុកទំនិញ!")
    await admin_products_menu(update, context)

# --- Broadcast System ---

async def admin_broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Initiates broadcast message prompt.
    """
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return

    await query.answer()
    text = (
        f"📢 <b>ផ្ញើសារប្រកាសទៅកាន់អតិថិជនទាំងអស់ / Broadcast Announcement</b>\n\n"
        f"សូមវាយបញ្ចូលសារដែលអ្នកចង់ផ្ញើទៅកាន់អតិថិជនទាំងអស់ (គាំទ្រអត្ថបទ រូបភាព ឬព័ត៌មានប្រូម៉ូសិន)៖\n\n"
        f"<i>វាយ /cancel ប្រសិនបើអ្នកចង់បោះបង់</i>"
    )
    await query.edit_message_text(text, parse_mode="HTML")
    return ADMIN_BROADCAST_STATE

async def admin_broadcast_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sends broadcast message to all users in DB.
    """
    user = update.effective_user
    if not is_admin(user.id):
        return ConversationHandler.END

    message_text = update.message.text
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()

    sent_count = 0
    fail_count = 0

    broadcast_header = f"📢 <b>សេចក្តីជូនដំណឹងពី {config.STORE_NAME_KH}:</b>\n\n{message_text}"

    status_msg = await update.message.reply_text(f"⏳ កំពុងផ្ញើសារទៅកាន់អតិថិជន {len(users)} នាក់...")

    for u in users:
        u_id = u["user_id"]
        try:
            await context.application.bot.send_message(
                chat_id=u_id,
                text=broadcast_header,
                parse_mode="HTML"
            )
            sent_count += 1
        except Exception:
            fail_count += 1

    await status_msg.edit_text(
        f"✅ <b>ការផ្ញើសារប្រកាសបានបញ្ចប់!</b>\n\n"
        f"📤 បានផ្ញើជោគជ័យ: {sent_count} នាក់\n"
        f"⚠️ បរាជ័យ (Block bot/inactive): {fail_count} នាក់",
        parse_mode="HTML"
    )
    return ConversationHandler.END

async def admin_broadcast_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ បានបោះបង់ការផ្ញើសារប្រកាស។")
    return ConversationHandler.END

def get_broadcast_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_broadcast_prompt, pattern="^admin_broadcast$")
        ],
        states={
            ADMIN_BROADCAST_STATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_send)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", admin_broadcast_cancel)
        ],
        per_message=False
    )

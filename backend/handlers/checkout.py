import time
import logging
import asyncio
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

import config
import database
import keyboards
import payment

logger = logging.getLogger(__name__)

# Conversation States
ASK_NAME, ASK_PHONE, ASK_ADDRESS, ASK_NOTE, CONFIRM_ORDER = range(5)

async def checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Starts checkout flow when user clicks 'Checkout' from cart.
    """
    user = update.effective_user
    cart_summary = database.get_cart_summary(user.id)

    if not cart_summary["items"]:
        msg = "🛒 កន្ត្រករបស់អ្នកនៅទទេ! សូមជ្រើសរើសទំនិញជាមុនសិន។"
        if update.callback_query:
            await update.callback_query.answer(msg, show_alert=True)
        else:
            await update.message.reply_text(msg)
        return ConversationHandler.END

    db_user = database.get_user(user.id) or {}
    context.user_data["checkout"] = {
        "user_id": user.id,
        "items": cart_summary["items"],
        "total_amount": cart_summary["total_amount"],
        "default_name": user.full_name or "Valued Customer",
        "default_phone": db_user.get("phone", ""),
        "default_address": db_user.get("address", "")
    }

    # Prompt for Name
    prompt_text = (
        f"📝 <b>ជំហានទី ១/៤: ព័ត៌មានអ្នកទទួល (Step 1/4: Recipient Name)</b>\n\n"
        f"សូមបញ្ចូលឈ្មោះរបស់អ្នកទទួល ឬជ្រើសរើសប៊ូតុងខាងក្រោម៖\n"
        f"<i>Please provide recipient name:</i>"
    )

    name_markup = ReplyKeyboardMarkup([
        [KeyboardButton(f"👤 {user.full_name}")],
        [KeyboardButton("❌ បោះបង់ការកុម្ម៉ង់ / Cancel")]
    ], resize_keyboard=True, one_time_keyboard=True)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_html(prompt_text, reply_markup=name_markup)
    else:
        await update.message.reply_html(prompt_text, reply_markup=name_markup)

    return ASK_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "បោះបង់" in text or "Cancel" in text:
        return await cancel_checkout(update, context)

    # Clean text if clicked on predefined button
    name = text.replace("👤", "").strip()
    context.user_data["checkout"]["delivery_name"] = name

    # Prompt for Phone
    prompt_text = (
        f"📱 <b>ជំហានទី ២/៤: លេខទូរស័ព្ទទំនាក់ទំនង (Step 2/4: Phone Number)</b>\n\n"
        f"សូមចុចប៊ូតុង '📲 ចែករំលែកលេខទូរស័ព្ទ' ខាងក្រោម ឬវាយបញ្ចូលលេខទូរស័ព្ទរបស់អ្នក (ឧទាហរណ៍: 012 345 678)៖\n"
        f"<i>Please share or type your contact phone number:</i>"
    )

    phone_markup = ReplyKeyboardMarkup([
        [KeyboardButton("📲 ចែករំលែកលេខទូរស័ព្ទ / Share Contact", request_contact=True)],
        [KeyboardButton("❌ បោះបង់ការកុម្ម៉ង់ / Cancel")]
    ], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_html(prompt_text, reply_markup=phone_markup)
    return ASK_PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"):
            phone = f"+{phone}"
    else:
        text = update.message.text.strip()
        if "បោះបង់" in text or "Cancel" in text:
            return await cancel_checkout(update, context)
        phone = text

    context.user_data["checkout"]["delivery_phone"] = phone

    # Prompt for Address
    last_addr = context.user_data["checkout"].get("default_address")
    prompt_text = (
        f"📍 <b>ជំហានទី ៣/៤: អាសយដ្ឋានដឹកជញ្ជូន (Step 3/4: Delivery Address)</b>\n\n"
        f"សូមបញ្ចូលទីតាំង ឬអាសយដ្ឋានដឹកជញ្ជូនរបស់អ្នក (ផ្ទះលេខ, ផ្លូវ, សង្កាត់, ខណ្ឌ ឬខេត្ត)៖\n"
        f"<i>Enter your delivery address in Phnom Penh or Province:</i>"
    )

    buttons = []
    if last_addr:
        buttons.append([KeyboardButton(f"📍 {last_addr}")])
    buttons.append([KeyboardButton("❌ បោះបង់ការកុម្ម៉ង់ / Cancel")])

    address_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_html(prompt_text, reply_markup=address_markup)
    return ASK_ADDRESS

async def receive_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "បោះបង់" in text or "Cancel" in text:
        return await cancel_checkout(update, context)

    address = text.replace("📍", "").strip()
    context.user_data["checkout"]["delivery_address"] = address

    # Prompt for Note
    prompt_text = (
        f"📝 <b>ជំហានទី ៤/៤: ចំណាំបន្ថែម (Step 4/4: Order Note / Optional)</b>\n\n"
        f"តើអ្នកមានចំណាំអ្វីបន្ថែមទេ? (ឧទាហរណ៍: ទឹកក្រឡុកផ្អែមតិច, ដាក់ម្ទេសច្រើន, ហៅទូរស័ព្ទមុនមកដល់)\n"
        f"ប្រសិនបើគ្មានទេ សូមចុច <b>'⏩ រំលង / Skip'</b>៖"
    )

    note_markup = ReplyKeyboardMarkup([
        [KeyboardButton("⏩ រំលង / Skip Note")],
        [KeyboardButton("❌ បោះបង់ការកុម្ម៉ង់ / Cancel")]
    ], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_html(prompt_text, reply_markup=note_markup)
    return ASK_NOTE

async def receive_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if "បោះបង់" in text or "Cancel" in text:
        return await cancel_checkout(update, context)

    if "រំលង" in text or "Skip" in text:
        note = ""
    else:
        note = text

    context.user_data["checkout"]["delivery_note"] = note

    # Save to user profile in DB for convenience next time
    user = update.effective_user
    delivery_info = context.user_data["checkout"]
    database.update_user_profile(
        user_id=user.id,
        phone=delivery_info["delivery_phone"],
        address=delivery_info["delivery_address"]
    )

    # Show Final Review and Confirmation
    total_usd = delivery_info["total_amount"]
    total_khr = int(total_usd * config.KHR_EXCHANGE_RATE)

    items_list_str = ""
    for item in delivery_info["items"]:
        items_list_str += f" • {item['name_kh']} x {item['quantity']} ({item['unit']}) = ${item['subtotal']:.2f}\n"

    review_text = (
        f"🧾 <b>ពិនិត្យមើលព័ត៌មានកុម្ម៉ង់ / Order Review</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>អ្នកទទួល / Recipient:</b> {delivery_info['delivery_name']}\n"
        f"📱 <b>លេខទូរស័ព្ទ / Phone:</b> {delivery_info['delivery_phone']}\n"
        f"📍 <b>ទីតាំងដឹក / Address:</b> {delivery_info['delivery_address']}\n"
        f"📝 <b>ចំណាំ / Note:</b> {note if note else 'គ្មាន (None)'}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🛒 <b>មុខទំនិញ / Items:</b>\n{items_list_str}"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>ទឹកប្រាក់សរុប / Total:</b> <b>${total_usd:.2f} USD</b> (~ {total_khr:,} ៛)\n\n"
        f"💡 <i>សូមចុចប៊ូតុងខាងក្រោមដើម្បីបង្កើតកូដ KHQR សម្រាប់ទូទាត់ប្រាក់តាម ABA Mobile៖</i>"
    )

    inline_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ បញ្ជាក់ & បង្កើត QR បង់ប្រាក់ / Confirm & Pay", callback_data="confirm_pay_khqr")],
        [InlineKeyboardButton("❌ បោះបង់ការកុម្ម៉ង់ / Cancel", callback_data="cancel_checkout_cb")]
    ])

    # Remove reply keyboard temporarily
    await update.message.reply_text("កំពុងបង្កើតសេចក្តីសង្ខេប...", reply_markup=ReplyKeyboardRemove())
    await update.message.reply_html(review_text, reply_markup=inline_markup)
    return CONFIRM_ORDER

async def confirm_payment_and_generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    User clicks 'Confirm & Pay' -> Creates order in DB -> calls AnajakPay -> sends KHQR image -> starts poller
    """
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    delivery_info = context.user_data.get("checkout")

    if not delivery_info:
        await query.edit_message_text("❌ មានបញ្ហាបាត់បង់ព័ត៌មាន។ សូមសាកល្បងម្ដងទៀត។")
        return ConversationHandler.END

    # Generate unique transaction id
    tx_id = f"FOOD_{int(time.time())}_{user.id}"

    order_id = database.create_order(
        user_id=user.id,
        transaction_id=tx_id,
        delivery_name=delivery_info["delivery_name"],
        delivery_phone=delivery_info["delivery_phone"],
        delivery_address=delivery_info["delivery_address"],
        delivery_note=delivery_info.get("delivery_note", "")
    )

    if not order_id:
        await query.edit_message_text("❌ កន្ត្រកទំនិញរបស់អ្នកនៅទទេ ឬមានបញ្ហាក្នុងការបង្កើតការកុម្ម៉ង់។")
        return ConversationHandler.END

    await query.edit_message_text("⏳ កំពុងភ្ជាប់ទៅកាន់ ABA Pay KHQR Gateway... សូមរង់ចាំមួយភ្លែត...")

    # Call AnajakPay KHQR API
    total_usd = delivery_info["total_amount"]
    remark = f"Order #{order_id} by {user.username or user.first_name}"
    pay_res = await payment.create_khqr_payment(
        transaction_id=tx_id,
        amount=total_usd,
        remark=remark
    )

    total_khr = int(total_usd * config.KHR_EXCHANGE_RATE)

    if not pay_res.get("success"):
        err_msg = pay_res.get("error", "Gateway connection error")
        await query.message.reply_html(
            f"⚠️ <b>មិនអាចបង្កើត QR Code បានទេ:</b> {err_msg}\n\n"
            f"សូមទាក់ទងមកកាន់អ្នកគ្រប់គ្រងតាមរយៈ @{config.STORE_CONTACT_USERNAME} ដើម្បីទទួលបានជំនួយ។"
        )
        return ConversationHandler.END

    qr_code_str = pay_res.get("qr", "")
    qr_url = pay_res.get("qr_url", "")

    caption_text = (
        f"🇰🇭 <b>ស្កេនទូទាត់ប្រាក់តាម KHQR / ABA Pay</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>វិក្កយបត្រ / Order ID:</b> #{order_id}\n"
        f"🔖 <b>លេខកូដប្រតិបត្តិការ:</b> <code>{tx_id}</code>\n"
        f"💵 <b>ចំនួនទឹកប្រាក់ / Amount:</b> <b>${total_usd:.2f} USD</b> (~ {total_khr:,} ៛)\n"
        f"🏪 <b>គណនីទទួល:</b> Hak Store by M.THY (ABA Bank)\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>របៀបបង់ប្រាក់ / How to Pay:</b>\n"
        f"1. បើកកម្មវិធី <b>ABA Mobile</b> ឬកម្មវិធីធនាគារនានាក្នុងប្រទេសកម្ពុជា\n"
        f"2. ស្កេនរូបភាព QR Code ខាងលើនេះ\n"
        f"3. ផ្ទៀងផ្ទាត់ឈ្មោះ និងចំនួនទឹកប្រាក់ រួចបញ្ជាក់ការទូទាត់\n\n"
        f"⚡ <i>ប្រព័ន្ធនឹងផ្ទៀងផ្ទាត់ដោយស្វ័យប្រវត្តិក្នងរយៈពេល ២-៣ វិនាទីក្រោយពេលលោកអ្នកបង់ប្រាក់រួច!</i>"
    )

    pay_keyboard = keyboards.get_payment_keyboard(tx_id)

    # Send QR photo (generate locally from EMV string or use URL)
    try:
        if qr_code_str:
            qr_bytes = payment.generate_local_qr_bytes(qr_code_str)
            await query.message.reply_photo(
                photo=qr_bytes,
                caption=caption_text,
                reply_markup=pay_keyboard,
                parse_mode="HTML"
            )
        elif qr_url:
            await query.message.reply_photo(
                photo=qr_url,
                caption=caption_text,
                reply_markup=pay_keyboard,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"Error sending QR image: {e}")
        # Fallback to direct url link
        await query.message.reply_html(caption_text, reply_markup=pay_keyboard)

    # Restore main menu navigation
    is_admin = user.id in config.ADMIN_IDS
    await query.message.reply_text(
        "💡 អ្នកអាចចុចប៊ូតុង '🔄 ពិនិត្យការទូទាត់' បានគ្រប់ពេល ប្រសិនបើចង់ពិនិត្យស្ថានភាពភ្លាមៗ។",
        reply_markup=keyboards.get_main_menu_keyboard(is_admin)
    )

    # Start background payment poller task
    asyncio.create_task(
        payment.poll_payment_background(context.application, tx_id, user.id, order_id)
    )

    # Notify Admin of New Order (Pending)
    admin_pending_alert = (
        f"🔔 <b>មានការបញ្ជាទិញថ្មី (រង់ចាំការបង់ប្រាក់) / New Order Placed</b>\n\n"
        f"📦 <b>Order ID:</b> #{order_id}\n"
        f"🔖 <b>Transaction ID:</b> <code>{tx_id}</code>\n"
        f"💰 <b>Total:</b> ${total_usd:.2f}\n"
        f"👤 <b>Customer:</b> {delivery_info['delivery_name']} (@{user.username or 'N/A'})\n"
        f"📞 <b>Phone:</b> {delivery_info['delivery_phone']}\n"
        f"📍 <b>Address:</b> {delivery_info['delivery_address']}\n"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await context.application.bot.send_message(
                chat_id=admin_id,
                text=admin_pending_alert,
                parse_mode="HTML"
            )
        except Exception:
            pass

    return ConversationHandler.END

async def cancel_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels current checkout flow and restores main menu.
    """
    user = update.effective_user
    is_admin = user.id in config.ADMIN_IDS
    cancel_text = "❌ ការបញ្ជាទិញត្រូវបានបោះបង់។ ទំនិញរបស់អ្នកនៅតែរក្សាទុកក្នុងកន្ត្រក។"

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.reply_text(
            cancel_text,
            reply_markup=keyboards.get_main_menu_keyboard(is_admin)
        )
    elif update.message:
        await update.message.reply_text(
            cancel_text,
            reply_markup=keyboards.get_main_menu_keyboard(is_admin)
        )

    context.user_data.pop("checkout", None)
    return ConversationHandler.END

def get_checkout_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(checkout_start, pattern="^checkout_start$")
        ],
        states={
            ASK_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)
            ],
            ASK_PHONE: [
                MessageHandler(filters.CONTACT | (filters.TEXT & ~filters.COMMAND), receive_phone)
            ],
            ASK_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_address)
            ],
            ASK_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_note)
            ],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_payment_and_generate_qr, pattern="^confirm_pay_khqr$"),
                CallbackQueryHandler(cancel_checkout, pattern="^cancel_checkout_cb$")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_checkout),
            MessageHandler(filters.Regex("(?i)(cancel|បោះបង់)"), cancel_checkout)
        ],
        per_message=False
    )

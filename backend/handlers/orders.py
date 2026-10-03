import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

import config
import database
import keyboards
import payment

logger = logging.getLogger(__name__)

STATUS_TRANSLATIONS = {
    "PENDING": ("⏳ រង់ចាំការទូទាត់ប្រាក់", "Pending Payment"),
    "PAID": ("✅ បានបង់ប្រាក់រួចរាល់", "Paid / Confirmed"),
    "PROCESSING": ("👨‍🍳 កំពុងរៀបចំការវេចខ្ចប់", "Processing / Packing"),
    "DELIVERING": ("🛵 កំពុងដឹកជញ្ជូន", "Out for Delivery"),
    "COMPLETED": ("🎉 បានដឹកជញ្ជូនជោគជ័យ", "Completed"),
    "CANCELLED": ("❌ បានបោះបង់", "Cancelled")
}

async def my_orders_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Lists past orders for the customer.
    """
    user = update.effective_user
    orders = database.get_user_orders(user.id, limit=10)

    if not orders:
        text = (
            f"📦 <b>ប្រវត្តិបញ្ជាទិញ / Order History</b>\n\n"
            f"លោកអ្នកមិនទាន់មានប្រវត្តិបញ្ជាទិញនៅឡើយទេ។\n"
            f"<i>You have no previous orders yet.</i>"
        )
        if update.message:
            await update.message.reply_html(text)
        elif update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(text, parse_mode="HTML")
        return

    text = (
        f"📦 <b>ប្រវត្តិបញ្ជាទិញរបស់អ្នក / Your Orders:</b>\n\n"
        f"សូមជ្រើសរើសវិក្កយបត្រណាមួយខាងក្រោមដើម្បីមើលព័ត៌មានលម្អិត៖"
    )
    reply_markup = keyboards.get_orders_list_keyboard(orders)

    if update.message:
        await update.message.reply_html(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def view_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays full details of an order.
    Callback data: view_order_<tx_id>
    """
    query = update.callback_query
    await query.answer()

    tx_id = query.data.replace("view_order_", "")
    order = database.get_order_by_tx(tx_id)

    if not order:
        await query.answer("រកមិនឃើញការកុម្ម៉ង់នេះទេ!", show_alert=True)
        return

    kh_status, en_status = STATUS_TRANSLATIONS.get(order["status"], (order["status"], order["status"]))
    total_khr = int(order["total_amount"] * config.KHR_EXCHANGE_RATE)

    text_lines = [
        f"📦 <b>ព័ត៌មានវិក្កយបត្រ / Order Details #{order['order_id']}</b>",
        f"━━━━━━━━━━━━━━━━━━",
        f"🔖 <b>Transaction ID:</b> <code>{order['transaction_id']}</code>",
        f"🚦 <b>ស្ថានភាព / Status:</b> <b>{kh_status}</b> ({en_status})",
        f"📅 <b>កាលបរិច្ឆេទ / Date:</b> {order['created_at'][:19].replace('T', ' ')}",
        f"━━━━━━━━━━━━━━━━━━",
        f"👤 <b>អ្នកទទួល / Recipient:</b> {order['delivery_name']}",
        f"📱 <b>លេខទូរស័ព្ទ / Phone:</b> {order['delivery_phone']}",
        f"📍 <b>ទីតាំងដឹកជញ្ជូន:</b> {order['delivery_address']}",
        f"📝 <b>ចំណាំ / Note:</b> {order.get('delivery_note') or 'គ្មាន (None)'}",
        f"━━━━━━━━━━━━━━━━━━",
        f"🛒 <b>មុខទំនិញ / Order Items:</b>"
    ]

    for item in order.get("items", []):
        text_lines.append(f" • {item['product_name']} x {item['quantity']} ({item['unit']}) = ${item['subtotal']:.2f}")

    text_lines.append(f"━━━━━━━━━━━━━━━━━━")
    text_lines.append(f"💵 <b>តម្លៃសរុប / Total Amount:</b> <b>${order['total_amount']:.2f} USD</b> (~ {total_khr:,} ៛)")

    if order.get("paid_at"):
        text_lines.append(f"✅ <b>ទូទាត់រួចនៅម៉ោង:</b> {order['paid_at'][:19].replace('T', ' ')}")

    reply_markup = keyboards.get_order_actions_keyboard(order)
    await query.edit_message_text("\n".join(text_lines), reply_markup=reply_markup, parse_mode="HTML")

async def verify_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Manual verification triggered by user tapping [🔄 ពិនិត្យការទូទាត់ / Verify Payment]
    Callback data: verify_pay_<tx_id>
    """
    query = update.callback_query
    await query.answer("កំពុងពិនិត្យជាមួយធនាគារ ABA... / Checking with Bank...")

    tx_id = query.data.replace("verify_pay_", "")
    order = database.get_order_by_tx(tx_id)

    if not order:
        await query.answer("រកមិនឃើញវិក្កយបត្រនេះទេ!", show_alert=True)
        return

    if order["status"] in ["PAID", "PROCESSING", "DELIVERING", "COMPLETED"]:
        await query.answer("✅ វិក្កយបត្រនេះបានទូទាត់រួចរាល់ហើយ!", show_alert=True)
        await view_order_detail(update, context)
        return

    result = await payment.check_transaction_status(tx_id)

    if result.get("success") and result.get("status") == "success":
        paid_amount = result.get("amount") or order["total_amount"]
        khr_amount = int(float(paid_amount) * config.KHR_EXCHANGE_RATE)

        success_msg = (
            f"🎉 <b>ការទូទាត់ប្រាក់បានជោគជ័យ! / Payment Successful!</b>\n\n"
            f"✅ <b>វិក្កយបត្រ / Order ID:</b> #{order['order_id']} (<code>{tx_id}</code>)\n"
            f"💵 <b>ចំនួនទឹកប្រាក់:</b> ${float(paid_amount):.2f} (~ {khr_amount:,} ៛)\n"
            f"🏦 <b>ធនាគារ:</b> ABA Pay KHQR\n\n"
            f"🙏 សូមអរគុណ! ក្រុមការងារយើងខ្ញុំកំពុងរៀបចំ និងដឹកជញ្ជូនជូនលោកអ្នកយ៉ាងយកចិត្តទុកដាក់បំផុត!"
        )

        try:
            await query.message.reply_html(success_msg)
        except Exception:
            pass

        # Notify Admin
        admin_alert = (
            f"🚨 <b>ការបញ្ជាទិញត្រូវបានទូទាត់ជោគជ័យ! / ORDER PAID!</b>\n\n"
            f"📦 <b>Order ID:</b> #{order['order_id']}\n"
            f"🔖 <b>TX:</b> <code>{tx_id}</code>\n"
            f"💰 <b>Total:</b> ${float(paid_amount):.2f}\n"
            f"👤 <b>Customer:</b> {order['delivery_name']}\n"
            f"📞 <b>Phone:</b> {order['delivery_phone']}\n"
            f"📍 <b>Address:</b> {order['delivery_address']}\n"
        )
        for admin_id in config.ADMIN_IDS:
            try:
                await context.application.bot.send_message(
                    chat_id=admin_id,
                    text=admin_alert,
                    parse_mode="HTML"
                )
            except Exception:
                pass

        await view_order_detail(update, context)
    else:
        await query.answer(
            "⏳ មិនទាន់ទទួលបានការទូទាត់នៅឡើយទេ។ សូមប្រាកដថាអ្នកបានស្កេន និងបញ្ជាក់ការបង់ប្រាក់ក្នុង ABA Mobile រួចចុចពិនិត្យម្តងទៀត។",
            show_alert=True
        )

async def show_qr_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Re-displays KHQR code for a pending order.
    Callback data: show_qr_<tx_id>
    """
    query = update.callback_query
    await query.answer()

    tx_id = query.data.replace("show_qr_", "")
    order = database.get_order_by_tx(tx_id)

    if not order or order["status"] != "PENDING":
        await query.answer("វិក្កយបត្រនេះមិនស្ថិតក្នុងស្ថានភាពរង់ចាំបង់ប្រាក់ទេ!", show_alert=True)
        return

    total_khr = int(order["total_amount"] * config.KHR_EXCHANGE_RATE)
    caption_text = (
        f"🇰🇭 <b>ស្កេនទូទាត់ប្រាក់តាម KHQR / ABA Pay</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>វិក្កយបត្រ:</b> #{order['order_id']}\n"
        f"💵 <b>ចំនួនទឹកប្រាក់:</b> <b>${order['total_amount']:.2f} USD</b> (~ {total_khr:,} ៛)\n"
        f"🏪 <b>គណនីទទួល:</b> Hak Store by M.THY\n"
    )

    pay_keyboard = keyboards.get_payment_keyboard(tx_id)

    qr_str = order.get("payment_qr")
    qr_url = order.get("payment_qr_url")

    if qr_str:
        qr_bytes = payment.generate_local_qr_bytes(qr_str)
        await query.message.reply_photo(photo=qr_bytes, caption=caption_text, reply_markup=pay_keyboard, parse_mode="HTML")
    elif qr_url:
        await query.message.reply_photo(photo=qr_url, caption=caption_text, reply_markup=pay_keyboard, parse_mode="HTML")
    else:
        await query.message.reply_html(caption_text, reply_markup=pay_keyboard)

async def cancel_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Cancels an order if it is still PENDING.
    Callback data: cancel_order_<tx_id>
    """
    query = update.callback_query
    await query.answer()

    tx_id = query.data.replace("cancel_order_", "")
    order = database.get_order_by_tx(tx_id)

    if not order:
        await query.answer("រកមិនឃើញវិក្កយបត្រនេះទេ!", show_alert=True)
        return

    if order["status"] != "PENDING":
        await query.answer("មិនអាចបោះបង់ការកុម្ម៉ង់ដែលបានបង់ប្រាក់រួចហើយបានទេ!", show_alert=True)
        return

    database.update_order_status(tx_id, "CANCELLED")
    await query.answer("❌ បានបោះបង់ការកុម្ម៉ង់ដោយជោគជ័យ!", show_alert=True)
    await view_order_detail(update, context)

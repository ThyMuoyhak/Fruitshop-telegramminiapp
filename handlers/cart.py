import logging
from telegram import Update
from telegram.ext import ContextTypes

import config
import database
import keyboards

logger = logging.getLogger(__name__)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Renders user cart with itemized pricing, subtotal, and controls.
    """
    user = update.effective_user
    cart_summary = database.get_cart_summary(user.id)
    items = cart_summary["items"]

    if not items:
        empty_text = (
            f"🛒 <b>កន្ត្រកទំនិញរបស់អ្នកនៅទទេ! / Your Cart is Empty</b>\n\n"
            f"លោកអ្នកមិនទាន់បានជ្រើសរើសទំនិញនៅឡើយទេ។ សូមចូលទៅកាន់ស្តុកទំនិញដើម្បីជ្រើសរើសផ្លែឈើស្រស់ៗ និងអាហារខ្មែរឆ្ងាញ់ៗ!\n\n"
            f"<i>You haven't added any items to your cart yet.</i>"
        )
        categories = database.get_categories()
        reply_markup = keyboards.get_categories_keyboard(categories)

        if update.message:
            await update.message.reply_html(empty_text, reply_markup=reply_markup)
        elif update.callback_query:
            await update.callback_query.answer()
            try:
                await update.callback_query.message.delete()
            except Exception:
                pass
            await update.callback_query.message.reply_html(empty_text, reply_markup=reply_markup)
        return

    # Build cart summary text
    total_usd = cart_summary["total_amount"]
    total_khr = int(total_usd * config.KHR_EXCHANGE_RATE)

    text_lines = [
        f"🛒 <b>កន្ត្រកទំនិញរបស់អ្នក / Your Shopping Cart</b>",
        f"━━━━━━━━━━━━━━━━━━"
    ]

    for idx, item in enumerate(items, 1):
        item_total_khr = int(item['subtotal'] * config.KHR_EXCHANGE_RATE)
        text_lines.append(
            f"<b>{idx}. {item['name_kh']}</b> ({item['name_en']})\n"
            f"   ▫️ ចំនួន: <b>{item['quantity']}</b> x ${item['price']:.2f}/{item['unit']}\n"
            f"   ▫️ សរុប: <b>${item['subtotal']:.2f}</b> (~ {item_total_khr:,} ៛)"
        )

    text_lines.append(f"━━━━━━━━━━━━━━━━━━")
    text_lines.append(f"📦 <b>ចំនួនមុខទំនិញសរុប:</b> {cart_summary['total_items']} items")
    text_lines.append(f"💵 <b>តម្លៃសរុប / Total Amount:</b> <b>${total_usd:.2f} USD</b> (~ {total_khr:,} ៛)")
    text_lines.append(f"\n💡 <i>ចុច ➕ ឬ ➖ ដើម្បីកែសម្រួលចំនួន ឬចុច Checkout ដើម្បីបន្ត៖</i>")

    cart_text = "\n".join(text_lines)
    reply_markup = keyboards.get_cart_keyboard(items)

    if update.message:
        await update.message.reply_html(cart_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.delete()
        except Exception:
            pass
        await update.callback_query.message.reply_html(cart_text, reply_markup=reply_markup)

async def cart_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles inline cart actions: cart_inc_<id>, cart_dec_<id>, cart_del_<id>
    """
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split("_")
    action = parts[1]  # inc, dec, del
    product_id = int(parts[2])

    cart_items = {item["product_id"]: item for item in database.get_cart_items(user.id)}
    current_item = cart_items.get(product_id)

    if not current_item:
        await query.answer("ទំនិញនេះលែងមានក្នុងកន្ត្រកហើយ!", show_alert=True)
        await view_cart(update, context)
        return

    current_qty = current_item["quantity"]

    if action == "inc":
        database.update_cart_quantity(user.id, product_id, current_qty + 1)
        await query.answer("✅ បន្ថែមចំនួន +1")
    elif action == "dec":
        if current_qty > 1:
            database.update_cart_quantity(user.id, product_id, current_qty - 1)
            await query.answer("➖ បន្ថយចំនួន -1")
        else:
            database.remove_from_cart(user.id, product_id)
            await query.answer("🗑️ បានលុបទំនិញចេញពីកន្ត្រក")
    elif action == "del":
        database.remove_from_cart(user.id, product_id)
        await query.answer("🗑️ បានលុបទំនិញចេញពីកន្ត្រក")

    # Refresh cart view
    await view_cart(update, context)

async def cart_clear_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Clears all items in user's cart.
    """
    query = update.callback_query
    user = update.effective_user
    database.clear_cart(user.id)
    await query.answer("🗑️ កន្ត្រកទំនិញត្រូវបានសម្អាត!", show_alert=True)
    await view_cart(update, context)

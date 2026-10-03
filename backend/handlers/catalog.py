import logging
from telegram import Update
from telegram.ext import ContextTypes

import config
import database
import keyboards

logger = logging.getLogger(__name__)

async def store_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows categories list when clicking store button or typing command.
    """
    categories = database.get_categories()
    text = (
        f"🍎 <b>សូមជ្រើសរើសប្រភេទមុខទំនិញ / Choose Category:</b>\n\n"
        f"យើងមានផ្លែឈើស្រស់ៗធម្មជាតិ ទឹកផ្លែឈើក្រឡុក និងអាហារខ្មែរឆ្ងាញ់ៗជាច្រើនមុខ៖"
    )
    reply_markup = keyboards.get_categories_keyboard(categories)

    if update.message:
        await update.message.reply_html(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def category_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows products within a selected category.
    """
    query = update.callback_query
    await query.answer()

    category_id = int(query.data.split("_")[1])
    category = database.get_category(category_id)
    if not category:
        await query.answer("Category not found.", show_alert=True)
        return

    products = database.get_products_by_category(category_id, only_available=True)

    if not products:
        text = (
            f"{category.get('icon', '🍎')} <b>{category['name_kh']} ({category['name_en']})</b>\n\n"
            f"បច្ចុប្បន្នមុខទំនិញក្នុងផ្នែកនេះកំពុងដាច់ស្តុកបណ្តោះអាសន្ន។ សូមពិនិត្យមើលផ្នែកផ្សេងទៀត!\n"
            f"Currently no items available in this category."
        )
        reply_markup = keyboards.get_products_keyboard(category_id, [])
    else:
        text = (
            f"{category.get('icon', '🍎')} <b>{category['name_kh']} | {category['name_en']}</b>\n\n"
            f"ជ្រើសរើសមុខទំនិញដើម្បីមើលព័ត៌មានលម្អិត និងដាក់បញ្ចូលទៅក្នុងកន្ត្រក៖\n"
            f"<i>Select an item below to view details and add to cart:</i>"
        )
        reply_markup = keyboards.get_products_keyboard(category_id, products)

    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        # In case previous message had a photo
        await query.message.reply_html(text, reply_markup=reply_markup)

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays full details of an item with photo, description, price, and quantity selector.
    """
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("_")[1])
    product = database.get_product(product_id)

    if not product:
        await query.answer("Product not found.", show_alert=True)
        return

    khr_price = int(product["price"] * config.KHR_EXCHANGE_RATE)
    caption = (
        f"🏷️ <b>{product['name_kh']}</b>\n"
        f"<i>{product['name_en']}</i>\n\n"
        f"📝 <b>ការពិពណ៌នា / Description:</b>\n"
        f"{product['description_kh'] or product['description_en']}\n\n"
        f"💵 <b>តម្លៃ / Price:</b> <b>${product['price']:.2f}</b> / {product['unit']} (~ {khr_price:,} ៛)\n"
        f"📦 <b>ស្ថានភាពស្តុក / Status:</b> {'✅ មានក្នុងស្តុក (In Stock)' if product['is_available'] else '❌ ដាច់ស្តុក (Out of Stock)'}\n"
    )

    reply_markup = keyboards.get_product_detail_keyboard(product["id"], product["category_id"], quantity=1)

    # If product has an image url, send as photo with caption
    if product.get("image_url"):
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.message.reply_photo(
            photo=product["image_url"],
            caption=caption,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text(caption, reply_markup=reply_markup, parse_mode="HTML")

async def adjust_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles quantity increment/decrement for product view.
    Callback data: qty_plus_<prod_id>_<current_qty> or qty_minus_<prod_id>_<current_qty>
    """
    query = update.callback_query
    parts = query.data.split("_")
    action = parts[1]  # plus or minus
    product_id = int(parts[2])
    current_qty = int(parts[3])

    if action == "plus":
        new_qty = current_qty + 1
    else:
        new_qty = max(1, current_qty - 1)

    if new_qty == current_qty:
        await query.answer()
        return

    product = database.get_product(product_id)
    if not product:
        await query.answer()
        return

    reply_markup = keyboards.get_product_detail_keyboard(product_id, product["category_id"], quantity=new_qty)

    try:
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        await query.answer(f"ចំនួន: {new_qty}")
    except Exception as e:
        logger.debug(f"Error editing reply markup: {e}")
        await query.answer()

async def add_to_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Adds selected quantity to user's cart.
    Callback data: add_cart_<prod_id>_<qty>
    """
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split("_")
    product_id = int(parts[2])
    quantity = int(parts[3])

    product = database.get_product(product_id)
    if not product:
        await query.answer("Product not found.", show_alert=True)
        return

    total_qty = database.add_to_cart(user.id, product_id, quantity)
    await query.answer(
        f"✅ បានបញ្ចូល {product['name_kh']} ចំនួន {quantity} ទៅកាន់កន្ត្រក! (សរុប: {total_qty})",
        show_alert=True
    )

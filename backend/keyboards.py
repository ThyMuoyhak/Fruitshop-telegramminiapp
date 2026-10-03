from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from typing import List, Dict, Any
import config

def make_webapp_inline_button(text: str, url: str) -> InlineKeyboardButton:
    if url.startswith("https://"):
        return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))
    # Never pass http/localhost to url= parameter because Telegram API throws 'wrong http url'
    return InlineKeyboardButton(text=text, callback_data="open_shop_link")

def make_webapp_reply_button(text: str, url: str) -> KeyboardButton:
    if url.startswith("https://"):
        return KeyboardButton(text=text, web_app=WebAppInfo(url=url))
    return KeyboardButton(text=text)

def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Main persistent reply keyboard with ONLY 1 button: Open Shop.
    """
    keyboard = [
        [make_webapp_reply_button("🛍️ Open Shop", config.WEBAPP_URL)]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_miniapp_welcome_keyboard() -> InlineKeyboardMarkup:
    """
    Welcome inline keyboard with ONLY 1 button: Open Shop.
    """
    buttons = [
        [make_webapp_inline_button("🛍️ Open Shop", config.WEBAPP_URL)]
    ]
    return InlineKeyboardMarkup(buttons)

def get_categories_keyboard(categories: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Inline keyboard displaying fruit & food categories with MiniApp button.
    """
    buttons = [
        [make_webapp_inline_button("🛍️ បើកហាងពេញលេញ (Open MiniApp)", config.WEBAPP_URL)]
    ]
    for cat in categories:
        text = f"{cat.get('icon', '🍎')} {cat['name_kh']} | {cat['name_en']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"cat_{cat['id']}")])

    buttons.append([
        InlineKeyboardButton("🛒 មើលកន្ត្រក / View Cart", callback_data="view_cart"),
        InlineKeyboardButton("🔍 ជំនួយ / Help", callback_data="help_menu")
    ])
    return InlineKeyboardMarkup(buttons)

def get_products_keyboard(category_id: int, products: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Inline keyboard listing products in a category.
    """
    buttons = []
    for p in products:
        status_icon = "✅" if p.get("is_available") else "❌"
        text = f"{p['name_kh']} - ${p['price']:.2f}/{p['unit']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"prod_{p['id']}")])

    buttons.append([
        InlineKeyboardButton("⬅️ ប្រភេទទាំងអស់ / Categories", callback_data="all_categories"),
        InlineKeyboardButton("🛒 កន្ត្រក / Cart", callback_data="view_cart")
    ])
    return InlineKeyboardMarkup(buttons)

def get_product_detail_keyboard(product_id: int, category_id: int, quantity: int = 1) -> InlineKeyboardMarkup:
    """
    Product details interactive controls with quantity selector and Add to Cart.
    """
    buttons = [
        [
            InlineKeyboardButton("➖", callback_data=f"qty_minus_{product_id}_{quantity}"),
            InlineKeyboardButton(f"🔢 ចំនួន: {quantity}", callback_data="ignore"),
            InlineKeyboardButton("➕", callback_data=f"qty_plus_{product_id}_{quantity}")
        ],
        [
            InlineKeyboardButton(f"🛒 បញ្ចូលទៅកន្ត្រក / Add ({quantity})", callback_data=f"add_cart_{product_id}_{quantity}")
        ],
        [
            InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ / Back", callback_data=f"cat_{category_id}"),
            InlineKeyboardButton("🛒 មើលកន្ត្រក / Cart", callback_data="view_cart")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_cart_keyboard(cart_items: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Interactive Cart keyboard to modify quantities or proceed to checkout.
    """
    buttons = []
    for item in cart_items:
        p_id = item["product_id"]
        qty = item["quantity"]
        name = item["name_kh"]
        # Compact controls row per item: [➖] [ Item Name (qty) ] [➕]
        buttons.append([
            InlineKeyboardButton("➖", callback_data=f"cart_dec_{p_id}"),
            InlineKeyboardButton(f"{name} x {qty}", callback_data=f"prod_{p_id}"),
            InlineKeyboardButton("➕", callback_data=f"cart_inc_{p_id}"),
            InlineKeyboardButton("❌", callback_data=f"cart_del_{p_id}")
        ])

    buttons.append([
        InlineKeyboardButton("🛍️ បញ្ជាទិញ & បង់ប្រាក់ / Checkout", callback_data="checkout_start")
    ])
    buttons.append([
        InlineKeyboardButton("🗑️ សម្អាតកន្ត្រក / Clear", callback_data="cart_clear"),
        InlineKeyboardButton("🍎 បន្តទិញ / Continue Shopping", callback_data="all_categories")
    ])
    return InlineKeyboardMarkup(buttons)

def get_payment_keyboard(transaction_id: str) -> InlineKeyboardMarkup:
    """
    Keyboard shown with KHQR payment screen.
    """
    checkout_url = f"{config.CHECKOUT_FRONTEND_URL}?tx={transaction_id}"
    buttons = [
        [
            InlineKeyboardButton("🔄 ពិនិត្យការទូទាត់ / Verify Payment", callback_data=f"verify_pay_{transaction_id}")
        ],
        [
            InlineKeyboardButton("📲 បើក ABA Pay / Web Checkout", url=checkout_url)
        ],
        [
            InlineKeyboardButton("❌ បោះបង់ការកុម្ម៉ង់ / Cancel Order", callback_data=f"cancel_order_{transaction_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_orders_list_keyboard(orders: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Keyboard listing past orders.
    """
    buttons = []
    status_icons = {
        "PENDING": "⏳ រង់ចាំបង់ប្រាក់",
        "PAID": "✅ បានបង់ប្រាក់",
        "PROCESSING": "👨‍🍳 កំពុងរៀបចំ",
        "DELIVERING": "🛵 កំពុងដឹកជញ្ជូន",
        "COMPLETED": "🎉 បានបញ្ចប់",
        "CANCELLED": "❌ បានបោះបង់"
    }
    for o in orders:
        status_text = status_icons.get(o["status"], o["status"])
        btn_text = f"#{o['order_id']} | ${o['total_amount']:.2f} ({status_text})"
        buttons.append([InlineKeyboardButton(btn_text, callback_data=f"view_order_{o['transaction_id']}")])

    buttons.append([InlineKeyboardButton("🏠 ត្រឡប់ទៅមឺនុយដើម / Main Menu", callback_data="menu_home")])
    return InlineKeyboardMarkup(buttons)

def get_order_actions_keyboard(order: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Actions for an individual order.
    """
    buttons = []
    tx = order["transaction_id"]
    if order["status"] == "PENDING":
        buttons.append([
            InlineKeyboardButton("🔄 ពិនិត្យការទូទាត់ / Check Payment", callback_data=f"verify_pay_{tx}"),
            InlineKeyboardButton("💳 បង្ហាញ QR / Show QR", callback_data=f"show_qr_{tx}")
        ])
        buttons.append([
            InlineKeyboardButton("❌ បោះបង់ / Cancel", callback_data=f"cancel_order_{tx}")
        ])

    buttons.append([
        InlineKeyboardButton("⬅️ ប្រវត្តិបញ្ជាទិញ / My Orders", callback_data="my_orders"),
        InlineKeyboardButton("🏠 មឺនុយដើម / Main Menu", callback_data="menu_home")
    ])
    return InlineKeyboardMarkup(buttons)

# --- Admin Keyboards ---

def get_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """
    Admin control center.
    """
    buttons = [
        [
            InlineKeyboardButton("📊 របាយការណ៍ & ស្ថិតិ / Sales Stats", callback_data="admin_stats"),
            InlineKeyboardButton("📦 ការកុម្ម៉ង់ / Orders", callback_data="admin_orders_menu")
        ],
        [
            InlineKeyboardButton("🍎 គ្រប់គ្រងទំនិញ / Manage Products", callback_data="admin_products"),
            InlineKeyboardButton("📢 ផ្ញើសារប្រកាស / Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("🔄 ធ្វើបច្ចុប្បន្នភាព / Refresh", callback_data="admin_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_admin_orders_filter_keyboard() -> InlineKeyboardMarkup:
    """
    Filter orders by status for admin.
    """
    buttons = [
        [
            InlineKeyboardButton("⏳ Pending", callback_data="admin_list_orders_PENDING"),
            InlineKeyboardButton("💰 Paid", callback_data="admin_list_orders_PAID")
        ],
        [
            InlineKeyboardButton("👨‍🍳 Processing", callback_data="admin_list_orders_PROCESSING"),
            InlineKeyboardButton("🛵 Delivering", callback_data="admin_list_orders_DELIVERING")
        ],
        [
            InlineKeyboardButton("✅ Completed", callback_data="admin_list_orders_COMPLETED"),
            InlineKeyboardButton("📋 All Orders", callback_data="admin_list_orders_ALL")
        ],
        [
            InlineKeyboardButton("⬅️ ត្រឡប់ក្រោយ / Admin Dashboard", callback_data="admin_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_admin_order_manage_keyboard(order_id: int, tx: str, current_status: str) -> InlineKeyboardMarkup:
    """
    Status change buttons for admin.
    """
    buttons = [
        [
            InlineKeyboardButton("👨‍🍳 Mark Processing", callback_data=f"adm_set_{tx}_PROCESSING"),
            InlineKeyboardButton("🛵 Mark Delivering", callback_data=f"adm_set_{tx}_DELIVERING")
        ],
        [
            InlineKeyboardButton("✅ Mark Completed", callback_data=f"adm_set_{tx}_COMPLETED"),
            InlineKeyboardButton("❌ Cancel Order", callback_data=f"adm_set_{tx}_CANCELLED")
        ],
        [
            InlineKeyboardButton("⬅️ Back to Orders", callback_data="admin_orders_menu"),
            InlineKeyboardButton("🏠 Admin Home", callback_data="admin_home")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

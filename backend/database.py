import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import config

def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        phone TEXT,
        address TEXT,
        language TEXT DEFAULT 'en',
        created_at TEXT
    )
    """)

    # Categories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_en TEXT NOT NULL,
        name_kh TEXT NOT NULL,
        icon TEXT DEFAULT '🍎',
        sort_order INTEGER DEFAULT 0
    )
    """)

    # Products Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        name_en TEXT NOT NULL,
        name_kh TEXT NOT NULL,
        description_en TEXT,
        description_kh TEXT,
        price REAL NOT NULL,
        unit TEXT DEFAULT 'kg',
        image_url TEXT,
        is_available INTEGER DEFAULT 1,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    """)

    # Cart Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cart (
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        updated_at TEXT,
        PRIMARY KEY (user_id, product_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )
    """)

    # Orders Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        status TEXT DEFAULT 'PENDING',
        delivery_name TEXT,
        delivery_phone TEXT,
        delivery_address TEXT,
        delivery_note TEXT,
        payment_qr TEXT,
        payment_qr_url TEXT,
        payment_md5 TEXT,
        created_at TEXT,
        paid_at TEXT,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    """)

    # Order Items Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER,
        product_name TEXT NOT NULL,
        unit TEXT,
        price REAL NOT NULL,
        quantity INTEGER NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders (order_id)
    )
    """)

    # Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()

    # Seed Default Categories and Products if empty
    cursor.execute("SELECT COUNT(*) as count FROM categories")
    if cursor.fetchone()["count"] == 0:
        seed_initial_data(conn)

    conn.close()

def seed_initial_data(conn):
    cursor = conn.cursor()
    categories_data = [
        ("Fresh Khmer Fruits", "ផ្លែឈើស្រស់ខ្មែរ", "🍎", 1),
        ("Dried & Preserved Fruits", "ផ្លែឈើក្រៀម & ដំណាប់", "🥭", 2),
        ("Fresh Juices & Smoothies", "ទឹកផ្លែឈើស្រស់ & ក្រឡុក", "🥤", 3),
        ("KH Snacks & Specialties", "អាហារសម្រន់ & ម្ហូបខ្មែរ", "🍱", 4),
        ("Fruit Gift Baskets", "កន្ត្រកផ្លែឈើសួស្តី", "🎁", 5),
    ]

    cursor.executemany("""
    INSERT INTO categories (name_en, name_kh, icon, sort_order)
    VALUES (?, ?, ?, ?)
    """, categories_data)
    conn.commit()

    # Fetch inserted category IDs
    cursor.execute("SELECT id, name_en FROM categories")
    cat_map = {row["name_en"]: row["id"] for row in cursor.fetchall()}

    products_data = [
        # Fresh Fruits
        (
            cat_map["Fresh Khmer Fruits"],
            "Kampot Durian (Monthong / Ri6)",
            "ធុរេនកំពត រសជាតិផ្អែមឈ្ងុយ",
            "Authentic Kampot premium durian, creamy texture and aromatic golden pulp.",
            "ធុរេនកំពតពិតៗ សាច់មាស ផ្អែមឈ្ងុយឆ្ងាញ់ មានគុណភាពខ្ពស់",
            7.50,
            "1 kg",
            "https://images.unsplash.com/photo-1587334274328-64186a80aeee?w=600",
            1
        ),
        (
            cat_map["Fresh Khmer Fruits"],
            "Battambang Sweet Oranges",
            "ក្រូចពោធិ៍សាត់ បាត់ដំបង",
            "Sweet and juicy natural oranges harvested from Battambang orchards.",
            "ក្រូចពោធិ៍សាត់ដាំនៅបាត់ដំបង ទឹកច្រើន ផ្អែមឆ្ងាញ់បែបធម្មជាតិ",
            3.20,
            "1 kg",
            "https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=600",
            1
        ),
        (
            cat_map["Fresh Khmer Fruits"],
            "Koh Pen Sweet Pomelo",
            "ក្រូចថ្លុងកោះប៉ែន កំពង់ចាម",
            "Famous seedless, crisp, sweet pink pomelo from Koh Pen, Kampong Cham.",
            "ក្រូចថ្លុងកោះប៉ែនល្បីប្រចាំខេត្តកំពង់ចាម ផ្អែមឆ្ងាញ់ គ្មានគ្រាប់",
            4.00,
            "1 piece",
            "https://images.unsplash.com/photo-1577234286642-fc512a5f8f11?w=600",
            1
        ),
        (
            cat_map["Fresh Khmer Fruits"],
            "Keo Romeat Mango (Ripe)",
            "ស្វាយកែវរមៀតទុំស្រស់",
            "Sweet fragrance, sun-ripened Cambodian Keo Romeat mango.",
            "ស្វាយកែវរមៀតទុំលើដើម ផ្អែមមុត ឈ្ងុយឆ្ងាញ់ជាប់ចិត្ត",
            2.50,
            "1 kg",
            "https://images.unsplash.com/photo-1553279768-865429fa0078?w=600",
            1
        ),
        (
            cat_map["Fresh Khmer Fruits"],
            "Queen Mangosteen",
            "មង្ឃុតស្រស់ សាច់សក្បុស",
            "Freshly picked queen of fruits, juicy sweet and refreshing segments.",
            "មង្ឃុតធម្មជាតិ សាច់សក្បុស ផ្អែមត្រជាក់បំបាត់ស្រេកទឹក",
            4.80,
            "1 kg",
            "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=600",
            1
        ),
        (
            cat_map["Fresh Khmer Fruits"],
            "Pailin Longan (Mien)",
            "មៀនប៉ៃលិន សាច់ក្រាស់",
            "Crisp, sweet, thick pulp Pailin longans with small seeds.",
            "មៀនប៉ៃលិនសាច់ក្រាស់ គ្រាប់តូច ស្រួយផ្អែមឆ្ងាញ់",
            3.00,
            "1 kg",
            "https://images.unsplash.com/photo-1528825871115-3581a5387919?w=600",
            1
        ),
        (
            cat_map["Fresh Khmer Fruits"],
            "Red Dragon Fruit",
            "ផ្លែស្រកានាគក្រហម",
            "Vibrant red-flesh dragon fruit, packed with antioxidants.",
            "ផ្លែស្រកានាគសាច់ក្រហមធម្មជាតិ សម្បូរវីតាមីន និងសារធាតុចិញ្ចឹម",
            2.80,
            "1 kg",
            "https://images.unsplash.com/photo-1527325678964-54921661f888?w=600",
            1
        ),

        # Dried & Preserved Fruits
        (
            cat_map["Dried & Preserved Fruits"],
            "Chewy Dried Mango (Low Sugar)",
            "ដំណាប់ស្វាយធម្មជាតិ (ស្ករទាប)",
            "Delicious chewy dried mango slices, no artificial coloring.",
            "ដំណាប់ស្វាយធម្មជាតិ រសជាតិឆ្ងាញ់ជូរអែម មិនប្រើជាតិគីមី",
            3.50,
            "250g pack",
            "https://images.unsplash.com/photo-1601004890684-d8cbf643f5f2?w=600",
            1
        ),
        (
            cat_map["Dried & Preserved Fruits"],
            "Crispy Banana Chips (Sweet & Salty)",
            "ចេកបំពងស្រួយ រសជាតិប្រៃផ្អែម",
            "Golden thinly sliced crispy banana chips seasoned to perfection.",
            "ចេកបំពងស្រួយស្រុប រសជាតិប្រៃផ្អែមឈ្ងុយឆ្ងាញ់",
            2.00,
            "200g bag",
            "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=600",
            1
        ),
        (
            cat_map["Dried & Preserved Fruits"],
            "Freeze-Dried Jackfruit Chips",
            "ខ្នុរបំពងក្រៀមស្រួយ",
            "Crispy crunchy natural jackfruit snacks without oil.",
            "ខ្នុរក្រៀមស្រួយ ឈ្ងុយឆ្ងាញ់ធម្មជាតិ ១០០%",
            4.00,
            "200g pack",
            "https://images.unsplash.com/photo-1596797038530-2c107229654b?w=600",
            1
        ),

        # Juices & Smoothies
        (
            cat_map["Fresh Juices & Smoothies"],
            "Signature Avocado Smoothie",
            "បឺរក្រឡុកពិសេស",
            "Fresh Mondulkiri avocado blended with condensed milk and ice.",
            "ផ្លែបឺរស្រស់មណ្ឌលគិរី ក្រឡុកឈ្ងុយឆ្ងាញ់ម៉ត់ខៃ",
            2.50,
            "1 cup (500ml)",
            "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=600",
            1
        ),
        (
            cat_map["Fresh Juices & Smoothies"],
            "Cold-Pressed Orange & Passion Juice",
            "ទឹកក្រូចច្របាច់ & ផាសិនស្រស់",
            "Refreshing blend of 100% pure fresh orange and passion fruit.",
            "ទឹកក្រូចស្រស់ច្របាច់ផ្សំជាមួយផាសិន ត្រជាក់ស្រស់ស្រាយ",
            2.20,
            "1 bottle (400ml)",
            "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=600",
            1
        ),
        (
            cat_map["Fresh Juices & Smoothies"],
            "Fresh Sugar Cane with Calamansi",
            "ទឹកអំពៅច្របាច់ក្រូចឆ្មារ",
            "Freshly squeezed sugarcane juice with a hint of tart calamansi.",
            "ទឹកអំពៅធម្មជាតិ ច្របាច់ក្រូចឆ្មារឈ្ងុយត្រជាក់បំបាត់ហត់",
            1.50,
            "1 cup (500ml)",
            "https://images.unsplash.com/photo-1556881286-fc6915169721?w=600",
            1
        ),

        # KH Snacks & Food
        (
            cat_map["KH Snacks & Specialties"],
            "Green Mango with Khmer Chili Salt Dip",
            "ស្វាយខ្ចីអំបិលម្ទេស កាពិ",
            "Sour green mango slices served with traditional spicy shrimp paste chili salt.",
            "ស្វាយខ្ចីស្រួយស្រួយ ញ៉ាំជាមួយអំបិលម្ទេស ឬកាពិបុករសជាតិដើម",
            2.00,
            "1 set",
            "https://images.unsplash.com/photo-1543339308-43e59d6b73a6?w=600",
            1
        ),
        (
            cat_map["KH Snacks & Specialties"],
            "Crispy Rice Crackers with Pork Floss",
            "បាយក្តាំងសាច់ផាត់ ទឹកប្រហុក",
            "Traditional golden rice crust topped with savory pork floss and scallion oil.",
            "បាយក្តាំងស្រួយស្រុប លាបខ្លាញ់ស្លឹកខ្ទឹម និងសាច់ផាត់ឈ្ងុយឆ្ងាញ់",
            3.00,
            "1 box",
            "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=600",
            1
        ),

        # Fruit Gift Baskets
        (
            cat_map["Fruit Gift Baskets"],
            "Khmer Prosperity Fruit Basket",
            "កន្ត្រកផ្លែឈើសិរីមង្គលពិសេស",
            "Deluxe handcrafted basket with Durian, Pomelo, Oranges, Mangoes & Grapes with silk ribbon.",
            "កន្ត្រកផ្លែឈើប្រណិត តុបតែងដោយបូ និងផ្កាស្រស់ ស័ក្តិសមជាកាដូជូនពរ",
            35.00,
            "1 basket",
            "https://images.unsplash.com/photo-1519996529931-28324d5a630e?w=600",
            1
        ),
    ]

    cursor.executemany("""
    INSERT INTO products (category_id, name_en, name_kh, description_en, description_kh, price, unit, image_url, is_available)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products_data)
    conn.commit()

# --- User Functions ---

def register_user(user_id: int, username: str, first_name: str, last_name: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO users (user_id, username, first_name, last_name, created_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username,
        first_name=excluded.first_name,
        last_name=excluded.last_name
    """, (user_id, username or "", first_name or "", last_name or "", datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_profile(user_id: int, phone: str = None, address: str = None, language: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    updates = []
    params = []
    if phone is not None:
        updates.append("phone = ?")
        params.append(phone)
    if address is not None:
        updates.append("address = ?")
        params.append(address)
    if language is not None:
        updates.append("language = ?")
        params.append(language)
    if updates:
        params.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?", params)
        conn.commit()
    conn.close()

# --- Category & Product Functions ---

def get_categories() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories ORDER BY sort_order ASC, id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_category(category_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories WHERE id = ?", (category_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_products_by_category(category_id: int, only_available: bool = True) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM products WHERE category_id = ?"
    params = [category_id]
    if only_available:
        query += " AND is_available = 1"
    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT p.*, c.name_en as category_name_en, c.name_kh as category_name_kh FROM products p JOIN categories c ON p.category_id = c.id WHERE p.id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_products() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT p.*, c.name_en as category_name FROM products p JOIN categories c ON p.category_id = c.id ORDER BY p.category_id, p.id")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def toggle_product_availability(product_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_available FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False
    new_val = 0 if row["is_available"] == 1 else 1
    cursor.execute("UPDATE products SET is_available = ? WHERE id = ?", (new_val, product_id))
    conn.commit()
    conn.close()
    return True

def update_product_price(product_id: int, new_price: float) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
    conn.commit()
    conn.close()
    return True

def add_product(category_id: int, name_en: str, name_kh: str, description_en: str, description_kh: str, price: float, unit: str, image_url: str = "", is_available: int = 1) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO products (category_id, name_en, name_kh, description_en, description_kh, price, unit, image_url, is_available)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (category_id, name_en, name_kh, description_en, description_kh, price, unit, image_url, is_available))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_product(product_id: int, category_id: int, name_en: str, name_kh: str, description_en: str, description_kh: str, price: float, unit: str, image_url: str, is_available: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE products SET
        category_id = ?,
        name_en = ?,
        name_kh = ?,
        description_en = ?,
        description_kh = ?,
        price = ?,
        unit = ?,
        image_url = ?,
        is_available = ?
    WHERE id = ?
    """, (category_id, name_en, name_kh, description_en, description_kh, price, unit, image_url, is_available, product_id))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

def delete_product(product_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    # Delete from cart first
    cursor.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

def add_category(name_en: str, name_kh: str, icon: str = "🍎", sort_order: int = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO categories (name_en, name_kh, icon, sort_order)
    VALUES (?, ?, ?, ?)
    """, (name_en, name_kh, icon, sort_order))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_category(category_id: int, name_en: str, name_kh: str, icon: str = "🍎", sort_order: int = 0) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE categories SET
        name_en = ?,
        name_kh = ?,
        icon = ?,
        sort_order = ?
    WHERE id = ?
    """, (name_en, name_kh, icon, sort_order, category_id))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

def delete_category(category_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    # Check if products exist in category
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE category_id = ?", (category_id,))
    count = cursor.fetchone()["count"]
    if count > 0:
        conn.close()
        return False
    cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    rows = cursor.rowcount
    conn.commit()
    conn.close()
    return rows > 0

# --- Cart Functions ---

def add_to_cart(user_id: int, product_id: int, quantity: int = 1) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO cart (user_id, product_id, quantity, updated_at)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(user_id, product_id) DO UPDATE SET
        quantity = quantity + excluded.quantity,
        updated_at = excluded.updated_at
    """, (user_id, product_id, quantity, datetime.now().isoformat()))
    conn.commit()
    cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    row = cursor.fetchone()
    total_qty = row["quantity"] if row else 0
    conn.close()
    return total_qty

def update_cart_quantity(user_id: int, product_id: int, quantity: int):
    conn = get_connection()
    cursor = conn.cursor()
    if quantity <= 0:
        cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    else:
        cursor.execute("""
        UPDATE cart SET quantity = ?, updated_at = ? WHERE user_id = ? AND product_id = ?
        """, (quantity, datetime.now().isoformat(), user_id, product_id))
    conn.commit()
    conn.close()

def remove_from_cart(user_id: int, product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    conn.commit()
    conn.close()

def clear_cart(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def get_cart_items(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.user_id, c.product_id, c.quantity,
           p.name_en, p.name_kh, p.price, p.unit, p.image_url,
           (c.quantity * p.price) as subtotal
    FROM cart c
    JOIN products p ON c.product_id = p.id
    WHERE c.user_id = ? AND p.is_available = 1
    ORDER BY c.updated_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_cart_summary(user_id: int) -> Dict[str, Any]:
    items = get_cart_items(user_id)
    total_items = sum(item["quantity"] for item in items)
    total_amount = sum(item["subtotal"] for item in items)
    return {
        "items": items,
        "total_items": total_items,
        "total_amount": round(total_amount, 2)
    }

# --- Order Functions ---

def create_order(user_id: int, transaction_id: str, delivery_name: str, delivery_phone: str, delivery_address: str, delivery_note: str = "") -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()

    items = get_cart_items(user_id)
    if not items:
        conn.close()
        return None

    total_amount = round(sum(item["subtotal"] for item in items), 2)
    now_iso = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO orders (transaction_id, user_id, total_amount, status, delivery_name, delivery_phone, delivery_address, delivery_note, created_at)
    VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
    """, (transaction_id, user_id, total_amount, delivery_name, delivery_phone, delivery_address, delivery_note or "", now_iso))
    order_id = cursor.lastrowid

    # Insert items
    for item in items:
        cursor.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, unit, price, quantity, subtotal)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_id, item["product_id"], item["name_en"], item["unit"], item["price"], item["quantity"], item["subtotal"]))

    # Clear user's cart
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()
    return order_id

def update_order_payment_info(transaction_id: str, qr_code: str, qr_url: str, md5: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE orders SET payment_qr = ?, payment_qr_url = ?, payment_md5 = ? WHERE transaction_id = ?
    """, (qr_code, qr_url, md5, transaction_id))
    conn.commit()
    conn.close()

def update_order_status(transaction_id: str, status: str, paid_at: str = None) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if paid_at:
        cursor.execute("UPDATE orders SET status = ?, paid_at = ? WHERE transaction_id = ?", (status, paid_at, transaction_id))
    else:
        cursor.execute("UPDATE orders SET status = ? WHERE transaction_id = ?", (status, transaction_id))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    return rows_affected > 0

def get_order_by_tx(transaction_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE transaction_id = ?", (transaction_id,))
    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return None

    order = dict(order_row)
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order["order_id"],))
    order["items"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return order

def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    order_row = cursor.fetchone()
    if not order_row:
        conn.close()
        return None

    order = dict(order_row)
    cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,))
    order["items"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return order

def get_user_orders(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM orders WHERE user_id = ? ORDER BY order_id DESC LIMIT ?
    """, (user_id, limit))
    orders = [dict(r) for r in cursor.fetchall()]
    for o in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["order_id"],))
        o["items"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return orders

def get_all_orders(status_filter: str = None, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if status_filter:
        cursor.execute("SELECT * FROM orders WHERE status = ? ORDER BY order_id DESC LIMIT ?", (status_filter, limit))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY order_id DESC LIMIT ?", (limit,))
    orders = [dict(r) for r in cursor.fetchall()]
    for o in orders:
        cursor.execute("SELECT * FROM order_items WHERE order_id = ?", (o["order_id"],))
        o["items"] = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return orders

def get_sales_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_orders, COALESCE(SUM(total_amount), 0) as total_revenue FROM orders WHERE status != 'CANCELLED'")
    row_all = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as paid_orders, COALESCE(SUM(total_amount), 0) as paid_revenue FROM orders WHERE status IN ('PAID', 'PROCESSING', 'DELIVERING', 'COMPLETED')")
    row_paid = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as pending_orders FROM orders WHERE status = 'PENDING'")
    row_pending = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    row_users = cursor.fetchone()

    conn.close()
    return {
        "total_orders": row_all["total_orders"],
        "total_revenue": round(row_all["total_revenue"], 2),
        "paid_orders": row_paid["paid_orders"],
        "paid_revenue": round(row_paid["paid_revenue"], 2),
        "pending_orders": row_pending["pending_orders"],
        "total_users": row_users["total_users"]
    }

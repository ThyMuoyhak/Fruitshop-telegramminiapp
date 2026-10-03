import sys
import os
import time
import shutil
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, Request, Form, UploadFile, File, Response, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
import database
import payment

logger = logging.getLogger("food_kh_backend")
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI App (Docs disabled for production security)
app = FastAPI(
    title="Food KH - Backend REST API",
    description="Decoupled REST API for Food KH Admin and Telegram MiniApp",
    version="2.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Enable CORS for decoupled React admin and MiniApp frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure upload directory exists and mount static uploads
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
app.mount("/static/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")

# Initialize database
database.init_db()

# --- Security & Auth ---
login_attempts: Dict[str, List[float]] = {}

def check_login_rate_limit(ip: str) -> bool:
    now = time.time()
    attempts = login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < 60]
    login_attempts[ip] = attempts
    return len(attempts) < 10

def is_authenticated(request: Request) -> bool:
    auth_header = request.headers.get("Authorization") or request.headers.get("X-Admin-Token")
    if auth_header:
        token = auth_header.replace("Bearer ", "").strip()
        if token == config.ADMIN_PASSWORD:
            return True
    cookie = request.cookies.get("admin_session")
    if cookie and cookie == config.ADMIN_PASSWORD:
        return True
    return False

def require_admin(request: Request):
    if not is_authenticated(request):
        raise HTTPException(
            status_code=401,
            detail="Admin authentication required. Invalid or missing token."
        )

# --- Telegram Bot Notification Helper ---
async def notify_telegram_admin(message: str):
    try:
        import httpx
        url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
        for admin_id in config.ADMIN_IDS:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json={
                    "chat_id": admin_id,
                    "text": message,
                    "parse_mode": "HTML"
                })
    except Exception as e:
        logger.error(f"Failed to notify Telegram admin: {e}")

# --- Helper Serializers ---
def serialize_product(p: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": p["id"],
        "category_id": p["category_id"],
        "name": p["name_en"],
        "name_en": p["name_en"],
        "name_kh": p["name_kh"],
        "description": p.get("description_en") or "",
        "description_en": p.get("description_en") or "",
        "description_kh": p.get("description_kh") or "",
        "price": p["price"],
        "price_usd": p["price"],
        "price_khr": int(p["price"] * 4100),
        "unit": p.get("unit") or "item",
        "image_url": p.get("image_url") or "",
        "is_available": p.get("is_available") == 1,
        "is_active": p.get("is_available") == 1,
        "category_name": p.get("category_name") or "",
    }

def serialize_category(c: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": c["id"],
        "name": c["name_en"],
        "name_en": c["name_en"],
        "name_kh": c["name_kh"],
        "icon": c.get("icon") or "🍎",
        "sort_order": c.get("sort_order") or 0,
    }

def serialize_order(o: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": o["order_id"],
        "order_id": o["order_id"],
        "transaction_id": o["transaction_id"],
        "telegram_user_id": o.get("user_id"),
        "customer_name": o.get("delivery_name") or f"Customer #{o.get('user_id')}",
        "customer_phone": o.get("delivery_phone") or "",
        "delivery_address": o.get("delivery_address") or "",
        "notes": o.get("delivery_note") or "",
        "total_usd": o["total_amount"],
        "total_khr": int(o["total_amount"] * 4100),
        "payment_method": "KHQR",
        "status": (o.get("status") or "PENDING").lower(),
        "created_at": o.get("created_at") or "",
        "paid_at": o.get("paid_at") or "",
        "items": [
            {
                "product_id": itm.get("product_id"),
                "product_name": itm.get("product_name"),
                "name": itm.get("product_name"),
                "unit": itm.get("unit"),
                "price": itm.get("price"),
                "price_usd": itm.get("price"),
                "quantity": itm.get("quantity"),
                "subtotal": itm.get("subtotal")
            }
            for itm in o.get("items", [])
        ]
    }

# ==========================================
# 1. Health & Root Info
# ==========================================
@app.get("/")
@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "Food KH Backend REST API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

# ==========================================
# 2. Authentication Endpoints
# ==========================================
class LoginSchema(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def api_login(request: Request, creds: LoginSchema):
    client_ip = request.client.host if request.client else "unknown"
    if not check_login_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many attempts. Please try again later.")

    if creds.username == config.ADMIN_USERNAME and creds.password == config.ADMIN_PASSWORD:
        return {
            "token": config.ADMIN_PASSWORD,
            "username": config.ADMIN_USERNAME,
            "role": "admin"
        }
    raise HTTPException(status_code=401, detail="Invalid username or password.")

@app.get("/api/auth/me")
async def api_auth_me(request: Request):
    require_admin(request)
    return {
        "username": config.ADMIN_USERNAME,
        "role": "admin",
        "status": "authenticated"
    }

@app.post("/api/auth/logout")
async def api_logout():
    return {"success": True}

# ==========================================
# 3. Analytics & Stats
# ==========================================
@app.get("/api/admin/stats")
async def api_admin_stats(request: Request):
    require_admin(request)
    stats = database.get_sales_stats()
    products = database.get_all_products()
    return {
        "total_revenue_usd": stats["paid_revenue"],
        "total_revenue_khr": int(stats["paid_revenue"] * 4100),
        "total_orders": stats["total_orders"],
        "pending_orders": stats["pending_orders"],
        "total_products": len(products),
        "total_users": stats.get("total_users", 0)
    }

# ==========================================
# 4. Products CRUD Endpoints
# ==========================================
class ProductCreateSchema(BaseModel):
    name: str
    name_kh: str
    category_id: Optional[int] = None
    price_usd: float
    price_khr: Optional[int] = None
    unit: Optional[str] = "item"
    description: Optional[str] = ""
    description_kh: Optional[str] = ""
    image_url: Optional[str] = ""
    is_active: Optional[bool] = True

@app.get("/api/products")
async def api_get_products(category_id: Optional[int] = None):
    if category_id:
        raw = database.get_products_by_category(category_id, only_available=False)
    else:
        raw = database.get_all_products()
    return [serialize_product(p) for p in raw]

@app.post("/api/products")
async def api_create_product(request: Request, data: ProductCreateSchema):
    require_admin(request)
    new_id = database.add_product(
        category_id=data.category_id or 1,
        name_en=data.name,
        name_kh=data.name_kh,
        description_en=data.description or "",
        description_kh=data.description_kh or "",
        price=data.price_usd,
        unit=data.unit or "item",
        image_url=data.image_url or "",
        is_available=1 if data.is_active else 0
    )
    prod = database.get_product(new_id)
    return serialize_product(prod) if prod else {"id": new_id}

@app.put("/api/products/{product_id}")
async def api_update_product(request: Request, product_id: int, data: ProductCreateSchema):
    require_admin(request)
    updated = database.update_product(
        product_id=product_id,
        category_id=data.category_id or 1,
        name_en=data.name,
        name_kh=data.name_kh,
        description_en=data.description or "",
        description_kh=data.description_kh or "",
        price=data.price_usd,
        unit=data.unit or "item",
        image_url=data.image_url or "",
        is_available=1 if data.is_active else 0
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Product not found")
    prod = database.get_product(product_id)
    return serialize_product(prod) if prod else {"id": product_id}

@app.patch("/api/products/{product_id}/toggle")
async def api_toggle_product(request: Request, product_id: int):
    require_admin(request)
    success = database.toggle_product_availability(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True}

@app.delete("/api/products/{product_id}")
async def api_delete_product(request: Request, product_id: int):
    require_admin(request)
    database.delete_product(product_id)
    return {"success": True}

# ==========================================
# 5. Categories CRUD Endpoints
# ==========================================
class CategoryCreateSchema(BaseModel):
    name: str
    name_kh: Optional[str] = ""
    icon: Optional[str] = "🍎"
    sort_order: Optional[int] = 0

@app.get("/api/categories")
async def api_get_categories():
    raw = database.get_categories()
    return [serialize_category(c) for c in raw]

@app.post("/api/categories")
async def api_create_category(request: Request, data: CategoryCreateSchema):
    require_admin(request)
    new_id = database.add_category(
        name_en=data.name,
        name_kh=data.name_kh or data.name,
        icon=data.icon or "📁",
        sort_order=data.sort_order or 0
    )
    cat = database.get_category(new_id)
    return serialize_category(cat) if cat else {"id": new_id}

@app.delete("/api/categories/{category_id}")
async def api_delete_category(request: Request, category_id: int):
    require_admin(request)
    deleted = database.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete category that contains products.")
    return {"success": True}

# ==========================================
# 6. Orders Endpoints
# ==========================================
@app.get("/api/orders")
async def api_get_orders(status: Optional[str] = None):
    raw = database.get_all_orders(status_filter=status.upper() if status else None, limit=100)
    return [serialize_order(o) for o in raw]

class OrderStatusSchema(BaseModel):
    status: str

@app.patch("/api/orders/{order_id}/status")
async def api_update_order_status(request: Request, order_id: int, data: OrderStatusSchema):
    require_admin(request)
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    database.update_order_status(order["transaction_id"], data.status.upper())
    return {"success": True, "status": data.status.lower()}

# ==========================================
# 7. MiniApp Checkout & QR Payment
# ==========================================
class OrderItemSchema(BaseModel):
    product_id: int
    quantity: int

class CheckoutSchema(BaseModel):
    user_id: Optional[int] = 0
    username: Optional[str] = ""
    name: str
    phone: str
    address: str
    note: Optional[str] = ""
    items: List[OrderItemSchema]

@app.post("/api/checkout")
async def api_checkout(data: CheckoutSchema):
    if not data.items:
        raise HTTPException(status_code=400, detail="Cart is empty")

    total_amount = 0.0
    items_to_save = []
    for itm in data.items:
        prod = database.get_product(itm.product_id)
        if prod and prod["is_available"]:
            sub = round(prod["price"] * itm.quantity, 2)
            total_amount += sub
            items_to_save.append({
                "product_id": prod["id"],
                "name": prod["name_en"],
                "unit": prod["unit"],
                "price": prod["price"],
                "quantity": itm.quantity,
                "subtotal": sub
            })

    total_amount = round(total_amount, 2)
    tx_id = f"FOOD_{int(time.time())}_{data.user_id or 1}"

    conn = database.get_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO orders (transaction_id, user_id, total_amount, status, delivery_name, delivery_phone, delivery_address, delivery_note, created_at)
    VALUES (?, ?, ?, 'PENDING', ?, ?, ?, ?, ?)
    """, (tx_id, data.user_id or 0, total_amount, data.name, data.phone, data.address, data.note or "", now_iso))
    order_id = cursor.lastrowid

    for itm in items_to_save:
        cursor.execute("""
        INSERT INTO order_items (order_id, product_id, product_name, unit, price, quantity, subtotal)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (order_id, itm["product_id"], itm["name"], itm["unit"], itm["price"], itm["quantity"], itm["subtotal"]))

    conn.commit()
    conn.close()

    # Generate KHQR with AnajakPay
    pay_res = await payment.create_khqr_payment(
        transaction_id=tx_id,
        amount=total_amount,
        remark=f"Order #{order_id} by {data.name}"
    )

    if not pay_res.get("success"):
        raise HTTPException(status_code=500, detail=pay_res.get("error", "Payment generation failed"))

    # Notify admin via Telegram
    admin_alert = (
        f"🔔 <b>[MiniApp] ការកុម្ម៉ង់ថ្មី (New MiniApp Order #{order_id})</b>\n\n"
        f"🔖 <b>TX:</b> <code>{tx_id}</code>\n"
        f"💰 <b>Total:</b> ${total_amount:.2f}\n"
        f"👤 <b>Customer:</b> {data.name}\n"
        f"📱 <b>Phone:</b> {data.phone}\n"
        f"📍 <b>Address:</b> {data.address}\n"
    )
    await notify_telegram_admin(admin_alert)

    return {
        "success": True,
        "order_id": order_id,
        "transaction_id": tx_id,
        "amount": total_amount,
        "qr": pay_res.get("qr"),
        "qr_url": pay_res.get("qr_url"),
        "checkout_url": f"{config.CHECKOUT_FRONTEND_URL}?tx={tx_id}"
    }

@app.get("/api/order/{tx_id}/status")
async def api_order_status(tx_id: str):
    order = database.get_order_by_tx(tx_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order["status"] in ["PAID", "PROCESSING", "DELIVERING", "COMPLETED"]:
        return {"status": "success", "order_status": order["status"]}

    res = await payment.check_transaction_status(tx_id)
    if res.get("success") and res.get("status") == "success":
        paid_alert = (
            f"🎉 <b>[MiniApp] ទូទាត់ជោគជ័យ! (PAYMENT SUCCESS)</b>\n\n"
            f"📦 <b>Order ID:</b> #{order['order_id']}\n"
            f"💰 <b>Paid Amount:</b> ${order['total_amount']:.2f}\n"
            f"👤 <b>Customer:</b> {order['delivery_name']}\n"
            f"📞 <b>Phone:</b> {order['delivery_phone']}\n"
            f"📍 <b>Address:</b> {order['delivery_address']}\n"
        )
        await notify_telegram_admin(paid_alert)
        return {"status": "success"}

    return {"status": "pending"}

@app.get("/api/qr-image")
async def api_qr_image(qr: str):
    buf = payment.generate_local_qr_bytes(qr)
    return StreamingResponse(buf, media_type="image/png")

# ==========================================
# 8. File Uploads
# ==========================================
@app.post("/api/upload")
async def api_upload_file(request: Request, file: UploadFile = File(...)):
    require_admin(request)
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    clean_filename = f"{int(time.time())}_{os.path.basename(file.filename).replace(' ', '_')}"
    filepath = os.path.join(config.UPLOAD_DIR, clean_filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "filename": clean_filename,
        "url": f"/static/uploads/{clean_filename}"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=False)

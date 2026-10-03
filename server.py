import sys
import os
import time
import shutil
import logging
from datetime import datetime

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
from typing import Optional, List, Dict
from fastapi import FastAPI, Request, Form, UploadFile, File, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
import database
import payment

logger = logging.getLogger("food_kh_server")
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI App (Docs, Redoc, and OpenAPI disabled for production security)
app = FastAPI(
    title="Food Fruit KH — MiniApp & Admin Dashboard",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
)

# Enable CORS for React Admin and MiniApp on separate origins/ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
os.makedirs(config.UPLOAD_DIR, exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

# Mount Static Files (Uploads directory mounted first to support persistent disk)
app.mount("/static/uploads", StaticFiles(directory=config.UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates Engine (Jinja2)
templates = Jinja2Templates(directory="templates")

# Initialize database
database.init_db()

# --- Auth & Security Helpers ---
login_attempts: Dict[str, List[float]] = {}

def check_login_rate_limit(ip: str) -> bool:
    now = time.time()
    attempts = login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < 60]
    login_attempts[ip] = attempts
    return len(attempts) < 8

def record_failed_login(ip: str):
    now = time.time()
    if ip not in login_attempts:
        login_attempts[ip] = []
    login_attempts[ip].append(now)

def is_authenticated(request: Request) -> bool:
    """
    Validates either the secure admin_session cookie or the X-Admin-Token header.
    """
    session_val = request.cookies.get("admin_session")
    auth_header = request.headers.get("X-Admin-Token") or request.headers.get("Authorization")
    token_val = auth_header.replace("Bearer ", "").strip() if auth_header else None
    return bool((session_val and session_val == config.ADMIN_PASSWORD) or (token_val and token_val == config.ADMIN_PASSWORD))

@app.middleware("http")
async def admin_security_middleware(request: Request, call_next):
    """
    Global Security Barrier:
    Enforces strict authentication on all /admin endpoints.
    Blocks any user or script from creating, modifying, or deleting products or categories.
    """
    path = request.url.path
    if path.startswith("/admin") and path != "/admin/login":
        if not is_authenticated(request):
            # If API/mutation request, immediately block with 401 Unauthorized JSON
            if request.method in ["POST", "PUT", "DELETE", "PATCH"] or "application/json" in request.headers.get("accept", ""):
                return JSONResponse(
                    {
                        "error": "Unauthorized",
                        "detail": "Admin authentication required. You cannot bypass or access this endpoint without logging in."
                    },
                    status_code=401
                )
            # Browser navigation redirect to login page
            return RedirectResponse(url="/admin/login?error=Access+denied.+Admin+login+required.", status_code=303)

    response = await call_next(request)
    return response

# --- Telegram Bot Notification Helper ---
async def notify_telegram_admin(message: str):
    """
    Sends message to admin Telegram ID via Bot API
    """
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

# ==========================================
# 1. Telegram MiniApp Frontend Routes
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def home_redirect():
    return RedirectResponse(url="/shop")

@app.get("/shop", response_class=HTMLResponse)
@app.get("/miniapp", response_class=HTMLResponse)
async def shop_miniapp(request: Request):
    """
    Renders modern Telegram MiniApp for customer shopping.
    """
    return templates.TemplateResponse(request=request, name="miniapp.html")

# --- Helper Serializers for React Admin & MiniApp ---
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
# 2. MiniApp API Endpoints
# ==========================================

@app.get("/api/categories")
async def api_get_categories():
    categories = database.get_categories()
    return JSONResponse([serialize_category(c) for c in categories])

@app.get("/api/products")
async def api_get_products(category_id: Optional[int] = None):
    if category_id:
        products = database.get_products_by_category(category_id, only_available=False)
    else:
        products = database.get_all_products()
    return JSONResponse([serialize_product(p) for p in products])

@app.get("/api/qr-image")
async def api_qr_image(qr: str):
    """
    Generates and streams high-res PNG image from raw KHQR EMV string
    """
    buf = payment.generate_local_qr_bytes(qr)
    return StreamingResponse(buf, media_type="image/png")

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
    """
    Receives order from MiniApp, creates record in SQLite, and generates AnajakPay KHQR code.
    """
    if not data.items:
        return JSONResponse({"success": False, "error": "No items in cart"}, status_code=400)

    # Calculate subtotal from products in DB
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

    # Insert into database
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

    # Call AnajakPay KHQR API
    remark = f"Order #{order_id} by {data.name}"
    pay_res = await payment.create_khqr_payment(
        transaction_id=tx_id,
        amount=total_amount,
        remark=remark
    )

    if not pay_res.get("success"):
        return JSONResponse({"success": False, "error": pay_res.get("error", "Payment error")}, status_code=500)

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

    checkout_url = f"{config.CHECKOUT_FRONTEND_URL}?tx={tx_id}"

    return JSONResponse({
        "success": True,
        "order_id": order_id,
        "transaction_id": tx_id,
        "amount": total_amount,
        "qr": pay_res.get("qr"),
        "qr_url": pay_res.get("qr_url"),
        "checkout_url": checkout_url
    })

@app.get("/api/order/{tx_id}/status")
async def api_order_status(tx_id: str):
    """
    Polls AnajakPay check API and returns payment status
    """
    order = database.get_order_by_tx(tx_id)
    if not order:
        return JSONResponse({"status": "not_found"}, status_code=404)

    if order["status"] in ["PAID", "PROCESSING", "DELIVERING", "COMPLETED"]:
        return JSONResponse({"status": "success", "order_status": order["status"]})

    res = await payment.check_transaction_status(tx_id)
    if res.get("success") and res.get("status") == "success":
        # Notify Admin of Payment Success
        paid_alert = (
            f"🎉 <b>[MiniApp] ទូទាត់ជោគជ័យ! (PAYMENT SUCCESS)</b>\n\n"
            f"📦 <b>Order ID:</b> #{order['order_id']}\n"
            f"💰 <b>Paid Amount:</b> ${order['total_amount']:.2f}\n"
            f"👤 <b>Customer:</b> {order['delivery_name']}\n"
            f"📞 <b>Phone:</b> {order['delivery_phone']}\n"
            f"📍 <b>Address:</b> {order['delivery_address']}\n"
        )
        await notify_telegram_admin(paid_alert)
        return JSONResponse({"status": "success"})

    return JSONResponse({"status": "pending"})

# ==========================================
# 2.5 REST API Endpoints for React Admin Portal
# ==========================================

class RestLoginSchema(BaseModel):
    username: str
    password: str

@app.post("/api/auth/login")
async def rest_api_login(request: Request, creds: RestLoginSchema):
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
async def rest_api_auth_me(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {
        "username": config.ADMIN_USERNAME,
        "role": "admin",
        "status": "authenticated"
    }

@app.post("/api/auth/logout")
async def rest_api_logout():
    return {"success": True}

@app.get("/api/admin/stats")
async def rest_api_admin_stats(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
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

class RestProductCreateSchema(BaseModel):
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

@app.post("/api/products")
async def rest_api_create_product(request: Request, data: RestProductCreateSchema):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
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
async def rest_api_update_product(request: Request, product_id: int, data: RestProductCreateSchema):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
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
async def rest_api_toggle_product(request: Request, product_id: int):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    database.toggle_product_availability(product_id)
    return {"success": True}

@app.delete("/api/products/{product_id}")
async def rest_api_delete_product(request: Request, product_id: int):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    database.delete_product(product_id)
    return {"success": True}

class RestCategoryCreateSchema(BaseModel):
    name: str
    name_kh: Optional[str] = ""
    icon: Optional[str] = "🍎"
    sort_order: Optional[int] = 0

@app.post("/api/categories")
async def rest_api_create_category(request: Request, data: RestCategoryCreateSchema):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    new_id = database.add_category(
        name_en=data.name,
        name_kh=data.name_kh or data.name,
        icon=data.icon or "📁",
        sort_order=data.sort_order or 0
    )
    cat = database.get_category(new_id)
    return serialize_category(cat) if cat else {"id": new_id}

@app.delete("/api/categories/{category_id}")
async def rest_api_delete_category(request: Request, category_id: int):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    deleted = database.delete_category(category_id)
    if not deleted:
        raise HTTPException(status_code=400, detail="Cannot delete category containing products.")
    return {"success": True}

@app.get("/api/orders")
async def rest_api_get_orders(status: Optional[str] = None):
    raw = database.get_all_orders(status_filter=status.upper() if status else None, limit=100)
    return [serialize_order(o) for o in raw]

class RestOrderStatusSchema(BaseModel):
    status: str

@app.patch("/api/orders/{order_id}/status")
async def rest_api_update_order_status(request: Request, order_id: int, data: RestOrderStatusSchema):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    order = database.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    database.update_order_status(order["transaction_id"], data.status.upper())
    return {"success": True, "status": data.status.lower()}

@app.post("/api/upload")
async def rest_api_upload_file(request: Request, file: UploadFile = File(...)):
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
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

# ==========================================
# 3. FastAPI MVT Admin Dashboard Routes
# ==========================================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = None):
    if is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(request=request, name="admin/login.html", context={"error": error})

@app.post("/admin/login")
async def admin_login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_login_rate_limit(client_ip):
        return RedirectResponse(url="/admin/login?error=Too+many+failed+attempts.+Please+wait+1+minute.", status_code=303)

    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="admin_session",
            value=config.ADMIN_PASSWORD,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7
        )
        return response

    record_failed_login(client_ip)
    return RedirectResponse(url="/admin/login?error=Invalid+Credentials", status_code=303)

@app.get("/admin/logout")
async def admin_logout():
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="admin_session")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard_view(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    stats = database.get_sales_stats()
    recent_orders = database.get_all_orders(limit=8)

    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context={
        "active_nav": "dashboard",
        "stats": stats,
        "recent_orders": recent_orders
    })

# --- Products Management ---

@app.get("/admin/products", response_class=HTMLResponse)
async def admin_products_list(request: Request, msg: Optional[str] = None):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    products = database.get_all_products()
    categories = database.get_categories()

    return templates.TemplateResponse(request=request, name="admin/products.html", context={
        "active_nav": "products",
        "products": products,
        "categories": categories,
        "message": msg
    })

@app.get("/admin/products/new", response_class=HTMLResponse)
async def admin_product_new_form(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    categories = database.get_categories()
    return templates.TemplateResponse(request=request, name="admin/product_form.html", context={
        "active_nav": "new_product",
        "categories": categories,
        "product": None
    })

@app.post("/admin/products/new")
async def admin_product_create(
    request: Request,
    category_id: int = Form(...),
    name_kh: str = Form(...),
    name_en: str = Form(...),
    price: float = Form(...),
    unit: str = Form(...),
    description_kh: Optional[str] = Form(""),
    description_en: Optional[str] = Form(""),
    image_url: Optional[str] = Form(""),
    is_available: Optional[int] = Form(1),
    image_file: Optional[UploadFile] = File(None)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)

    final_image_url = image_url or ""

    # Process file upload if provided
    if image_file and image_file.filename:
        filename = f"{int(time.time())}_{image_file.filename}"
        filepath = os.path.join(config.UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        final_image_url = f"/static/uploads/{filename}"

    database.add_product(
        category_id=category_id,
        name_en=name_en,
        name_kh=name_kh,
        description_en=description_en or "",
        description_kh=description_kh or "",
        price=price,
        unit=unit,
        image_url=final_image_url,
        is_available=is_available or 1
    )

    return RedirectResponse(url="/admin/products?msg=Product+created+successfully!", status_code=303)

@app.get("/admin/products/edit/{product_id}", response_class=HTMLResponse)
async def admin_product_edit_form(request: Request, product_id: int):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    product = database.get_product(product_id)
    if not product:
        return RedirectResponse(url="/admin/products", status_code=303)

    categories = database.get_categories()
    return templates.TemplateResponse(request=request, name="admin/product_form.html", context={
        "active_nav": "products",
        "categories": categories,
        "product": product
    })

@app.post("/admin/products/edit/{product_id}")
async def admin_product_update(
    request: Request,
    product_id: int,
    category_id: int = Form(...),
    name_kh: str = Form(...),
    name_en: str = Form(...),
    price: float = Form(...),
    unit: str = Form(...),
    description_kh: Optional[str] = Form(""),
    description_en: Optional[str] = Form(""),
    image_url: Optional[str] = Form(""),
    is_available: Optional[int] = Form(0),
    image_file: Optional[UploadFile] = File(None)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)

    existing = database.get_product(product_id)
    final_image_url = image_url or (existing.get("image_url") if existing else "")

    if image_file and image_file.filename:
        filename = f"{int(time.time())}_{image_file.filename}"
        filepath = os.path.join(config.UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(image_file.file, buffer)
        final_image_url = f"/static/uploads/{filename}"

    database.update_product(
        product_id=product_id,
        category_id=category_id,
        name_en=name_en,
        name_kh=name_kh,
        description_en=description_en or "",
        description_kh=description_kh or "",
        price=price,
        unit=unit,
        image_url=final_image_url,
        is_available=1 if is_available else 0
    )

    return RedirectResponse(url="/admin/products?msg=Product+updated+successfully!", status_code=303)

@app.post("/admin/products/toggle/{product_id}")
async def admin_product_toggle_stock(request: Request, product_id: int):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)
    database.toggle_product_availability(product_id)
    return RedirectResponse(url="/admin/products", status_code=303)

@app.post("/admin/products/delete/{product_id}")
async def admin_product_delete(request: Request, product_id: int):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)
    database.delete_product(product_id)
    return RedirectResponse(url="/admin/products?msg=Product+deleted+successfully!", status_code=303)

# --- Category Management ---

@app.get("/admin/categories", response_class=HTMLResponse)
async def admin_categories_list(request: Request, msg: Optional[str] = None):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    categories = database.get_categories()
    return templates.TemplateResponse(request=request, name="admin/categories.html", context={
        "active_nav": "categories",
        "categories": categories,
        "message": msg
    })

@app.post("/admin/categories/new")
async def admin_category_create(
    request: Request,
    name_kh: str = Form(...),
    name_en: str = Form(...),
    icon: str = Form("🍎"),
    sort_order: int = Form(0)
):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)
    database.add_category(name_en=name_en, name_kh=name_kh, icon=icon, sort_order=sort_order)
    return RedirectResponse(url="/admin/categories?msg=Category+added+successfully!", status_code=303)

@app.post("/admin/categories/delete/{category_id}")
async def admin_category_delete(request: Request, category_id: int):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)
    deleted = database.delete_category(category_id)
    if not deleted:
        return RedirectResponse(url="/admin/categories?msg=Cannot+delete+category+with+active+products!", status_code=303)
    return RedirectResponse(url="/admin/categories?msg=Category+deleted!", status_code=303)

# --- Orders Management ---

@app.get("/admin/orders", response_class=HTMLResponse)
async def admin_orders_list(request: Request, status: Optional[str] = None, msg: Optional[str] = None):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    orders = database.get_all_orders(status_filter=status, limit=40)
    return templates.TemplateResponse(request=request, name="admin/orders.html", context={
        "active_nav": "orders",
        "orders": orders,
        "current_status": status,
        "message": msg
    })

@app.post("/admin/orders/status/{tx_id}")
async def admin_update_order_status(request: Request, tx_id: str, status: str = Form(...)):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?error=Unauthorized", status_code=303)
    database.update_order_status(tx_id, status)
    return RedirectResponse(url="/admin/orders?msg=Order+status+updated!", status_code=303)

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting FastAPI Server on {config.SERVER_HOST}:{config.SERVER_PORT}...")
    print(f"🛍️ Telegram MiniApp: {config.WEBAPP_URL}")
    print(f"⚙️ Admin Dashboard: http://localhost:{config.SERVER_PORT}/admin")
    uvicorn.run("server:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=False)

import os
import time
import shutil
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import FastAPI, Request, Form, UploadFile, File, Response, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

import config
import database
import payment

logger = logging.getLogger("food_kh_server")
logging.basicConfig(level=logging.INFO)

# Initialize FastAPI App
app = FastAPI(title="Food Fruit KH — MiniApp & Admin Dashboard")

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

# --- Auth Helper ---
def is_authenticated(request: Request) -> bool:
    session_val = request.cookies.get("admin_session")
    return session_val == config.ADMIN_PASSWORD

def require_admin(request: Request):
    if not is_authenticated(request):
        raise HTTPException(status_code=303, detail="Redirect to login")

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

# ==========================================
# 2. MiniApp API Endpoints
# ==========================================

@app.get("/api/categories")
async def api_get_categories():
    categories = database.get_categories()
    return JSONResponse(categories)

@app.get("/api/products")
async def api_get_products(category_id: Optional[int] = None):
    if category_id:
        products = database.get_products_by_category(category_id, only_available=False)
    else:
        products = database.get_all_products()
    return JSONResponse(products)

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
# 3. FastAPI MVT Admin Dashboard Routes
# ==========================================

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: Optional[str] = None):
    if is_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(request=request, name="admin/login.html", context={"error": error})

@app.post("/admin/login")
async def admin_login_submit(username: str = Form(...), password: str = Form(...)):
    if username == config.ADMIN_USERNAME and password == config.ADMIN_PASSWORD:
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(key="admin_session", value=config.ADMIN_PASSWORD, httponly=True)
        return response
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
async def admin_product_toggle_stock(product_id: int):
    database.toggle_product_availability(product_id)
    return RedirectResponse(url="/admin/products", status_code=303)

@app.post("/admin/products/delete/{product_id}")
async def admin_product_delete(product_id: int):
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
    name_kh: str = Form(...),
    name_en: str = Form(...),
    icon: str = Form("🍎"),
    sort_order: int = Form(0)
):
    database.add_category(name_en=name_en, name_kh=name_kh, icon=icon, sort_order=sort_order)
    return RedirectResponse(url="/admin/categories?msg=Category+added+successfully!", status_code=303)

@app.post("/admin/categories/delete/{category_id}")
async def admin_category_delete(category_id: int):
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
async def admin_update_order_status(tx_id: str, status: str = Form(...)):
    database.update_order_status(tx_id, status)
    return RedirectResponse(url="/admin/orders?msg=Order+status+updated!", status_code=303)

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting FastAPI Server on {config.SERVER_HOST}:{config.SERVER_PORT}...")
    print(f"🛍️ Telegram MiniApp: {config.WEBAPP_URL}")
    print(f"⚙️ Admin Dashboard: http://localhost:{config.SERVER_PORT}/admin")
    uvicorn.run("server:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=False)

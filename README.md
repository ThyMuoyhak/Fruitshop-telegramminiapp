# 🍎 Food Fruit KH — Telegram Bot, MiniApp & FastAPI MVT Admin Dashboard

A unified e-commerce platform for fresh Cambodian fruits, snacks, and juices, featuring:
1. 🛍️ **Telegram MiniApp (Mini Shop)**: Embedded mobile web app inside Telegram.
2. 🤖 **Telegram Bot**: Conversational ordering, automated notifications & payment polling.
3. ⚙️ **FastAPI + SQLite MVT Admin Dashboard**: Full product CRUD, image upload, stock toggling, and order management.
4. 🇰🇭 **ABA Pay & KHQR Integration**: Powered by AnajakPay KHQRcc gateway.

---

## 🌟 Architecture Overview

```
                      +---------------------------------------+
                      |   Telegram Client (Mobile / Desktop)  |
                      +---------------------------------------+
                                   |               |
                         /start & bot text   MiniApp WebApp
                                   |               |
                                   v               v
            +---------------------------+     +-------------------------------+
            |  Telegram Bot (bot.py)    |     | FastAPI Server (server.py)    |
            |  python-telegram-bot v21  |     | - MiniApp: /shop              |
            +---------------------------+     | - Admin MVT: /admin           |
                         \                    | - JSON APIs: /api/*           |
                          \                   +-------------------------------+
                           \                                  /
                            v                                v
                  +---------------------------------------------------+
                  |         Shared SQLite Database (food_kh.db)       |
                  |     - Users, Products, Categories, Orders         |
                  +---------------------------------------------------+
                                            |
                                            v
                  +---------------------------------------------------+
                  |    AnajakPay KHQRcc Gateway (ABA Pay / Bakong)    |
                  |  - Direct QR API & Polling Verification V2        |
                  +---------------------------------------------------+
```

---

## 🚀 Key Features

### 1. 🛍️ Telegram MiniApp Store (`/shop`)
- **Direct Launch**: Tapping **"🛍️ បើកហាងទំនិញ / Open Shop"** opens the MiniApp directly inside Telegram.
- **Modern UI**: Tailored with Khmer and English typography (`Kantumruy Pro` & `Plus Jakarta Sans`).
- **Interactive Shopping**:
  - Filter by Categories: Fresh Fruits, Dried Fruits, Juices & Smoothies, KH Snacks, Gift Baskets.
  - Real-time product search.
  - Slide-up Cart Drawer with live subtotal calculation in USD ($) and KHR (៛).
- **One-Tap KHQR & ABA Pay Checkout**:
  - Auto-fills user details from Telegram profile (`initDataUnsafe.user`).
  - Calls `/api/checkout` to generate live KHQR code.
  - One-tap button: **Open in ABA Mobile**.
  - Automatic background polling every 3 seconds — detects payment immediately and displays celebratory confirmation 🎉!

---

### 2. ⚙️ FastAPI + SQLite MVT Admin Dashboard (`/admin`)
Access via browser at: **`http://localhost:8000/admin`**
- **Default Credentials**:
  - Username: `admin`
  - Password: `foodkh2026` *(Configurable in `.env`)*
- **Dashboard Overview**:
  - Real-time KPI statistics: Paid Revenue, Total Orders, Pending Orders, Total Users.
  - Recent orders table with customer info and quick status links.
- **Product Management (`/admin/products`)**:
  - Table of all products with image preview, names, prices ($ & ៛), and unit.
  - **1-Click Stock Toggle**: Switch products between `✅ មានក្នុងស្តុក (In Stock)` and `❌ ដាច់ស្តុក (Out of Stock)`.
  - **Add New Product (`/admin/products/new`)**:
    - Category selection.
    - Bilingual Name (Khmer & English) and Descriptions.
    - Price in USD and Unit.
    - Image URL or Direct File Upload (saved to `static/uploads/`).
    - Live image preview.
  - **Edit Product (`/admin/products/edit/{id}`)**: Update any field or image.
  - **Delete Product**: With confirmation safety check.
- **Category Management (`/admin/categories`)**:
  - View all categories with icons and sort order.
  - Add new categories.
- **Order Management (`/admin/orders`)**:
  - Filter orders by: `PENDING`, `PAID`, `PROCESSING`, `DELIVERING`, `COMPLETED`, `CANCELLED`.
  - Detailed breakdown of customer name, phone, delivery address, and ordered items.
  - 1-click status update.

---

### 3. 🤖 Telegram Bot Features (`@foodkhtestingbot`)
- **Chat Menu Button**: Permanent **🛍️ Shop** menu button in Telegram.
- **Chat Store**: Full catalog browsing and ordering directly inside chat conversation.
- **Admin Alerts**: Instant notifications sent to Thy Muoyhak (`1667587449`) when:
  - An order is placed (Pending)
  - An order is paid via ABA Mobile (Paid)

---

## 📁 Directory Structure

```
d:/Food KH/
├── config.py                 # Configuration & Environment Variables
├── database.py               # SQLite Schema, Queries & CRUD Helpers
├── payment.py                # AnajakPay KHQRcc Client & Verification
├── keyboards.py              # Telegram Keyboards with MiniApp Support
├── server.py                 # FastAPI Web Server (MiniApp + Admin Dashboard + APIs)
├── bot.py                    # Telegram Bot Application
├── run_all.py                # Unified Runner (Runs Server + Bot Concurrently)
├── run_bot.bat               # Windows 1-Click Launch Script
├── requirements.txt          # Python Dependencies
├── .env                      # Credentials & Configuration
├── static/
│   ├── uploads/              # Uploaded product images
│   ├── css/                  # Custom CSS styles
│   └── js/                   # Custom JavaScript
└── templates/
    ├── miniapp.html          # Telegram MiniApp Frontend Store
    └── admin/
        ├── base.html         # Admin Layout Template
        ├── dashboard.html    # Analytics & Recent Orders
        ├── products.html     # Products Table with Stock Toggles
        ├── product_form.html # Add & Edit Product Form
        ├── categories.html   # Category Management
        ├── orders.html       # Orders Management
        └── login.html        # Admin Login Page
```

---

## 🏃 Running the Application

### Option A: One-Click Runner (Recommended)
Double-click [`run_bot.bat`](file:///d:/Food%20KH/run_bot.bat) on Windows, or run:
```bash
python run_all.py
```
This automatically starts both:
- **FastAPI Web Server** at `http://localhost:8000`
- **Telegram Bot** polling `@foodkhtestingbot`

### Option B: Running Separately
- **Web Server Only**:
  ```bash
  python server.py
  ```
- **Telegram Bot Only**:
  ```bash
  python bot.py
  ```

---

## 📱 Testing MiniApp in Telegram Mobile (HTTPS Requirement)

Telegram requires an **HTTPS** URL for MiniApps to open inside the Telegram mobile app.
To expose your local server with free HTTPS in 10 seconds:

**Using Localtunnel (already installed via npx):**
```bash
npx localtunnel --port 8000
```
Copy the generated `https://xxxx.loca.lt` URL, open `.env` or `config.py` and set:
```env
WEBAPP_URL=https://xxxx.loca.lt/shop
```
Restart `run_all.py`, and your Telegram Bot will open the MiniApp in full-screen on any smartphone!

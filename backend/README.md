# Food KH — Backend REST API & Telegram Bot Engine

This directory contains the decoupled **Backend Service** for the Food KH platform. It provides a high-performance **FastAPI REST API**, an embedded **SQLite** database, an **AnajakPay KHQR** payment processing bridge, and an asynchronous **Telegram Bot** engine.

---

## 🚀 Features

- **FastAPI REST API**: Fully asynchronous, high-throughput endpoints for the React Admin Dashboard and Telegram MiniApp.
- **Cross-Origin Resource Sharing (CORS)**: Pre-configured to accept requests from any frontend domain (Vercel, Netlify, Render, Localhost).
- **Persistent SQLite**: Automatically mounts and detects Render Persistent Disk (`/var/data/food_kh.db`) with zero manual setup.
- **AnajakPay KHQR**: Dynamic generation of Cambodia standard EMV KHQR payment strings and real-time transaction polling.
- **Telegram Bot**: Asynchronous bot handling customer interactions, order notifications, and MiniApp launching.
- **Zero-Bypass Security**: Rate-limited admin authentication and protected inventory routes.

---

## 🛠️ Quick Start

### 1. Installation

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)

Copy `.env.example` to `.env` and fill in your keys:

```ini
# Bot Configuration
BOT_TOKEN=8834918127:AAGk6IK-SP_17chGe7b47IqVNob1ZftX_YM
ADMIN_IDS=123456789

# Web Server
PORT=8000
SERVER_HOST=0.0.0.0

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=foodkh2026

# AnajakPay KHQR Gateway
ANAJAK_MERCHANT_ID=your_merchant_id
ANAJAK_API_KEY=your_api_key
```

### 3. Running the Server

#### A. Run API Only (FastAPI)
```bash
python main.py
# Server runs on http://localhost:8000
```

#### B. Run Unified Worker (FastAPI + Telegram Bot in one process)
```bash
python bot_worker.py
```

---

## 📡 REST API Reference

### 🔐 Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Authenticate with username & password, returns bearer token |
| `GET` | `/api/auth/me` | Validate session / token |
| `POST` | `/api/auth/logout` | Invalidate session |

### 📊 Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/stats` | Total revenue (USD & KHR), order counts, active products |

### 🍏 Products Management
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/products` | Retrieve catalog (supports `?category_id=...`) |
| `POST` | `/api/products` | Create product (Requires Admin Token) |
| `PUT` | `/api/products/{id}` | Update product (Requires Admin Token) |
| `PATCH` | `/api/products/{id}/toggle` | Toggle in-stock / out-of-stock (Requires Admin Token) |
| `DELETE` | `/api/products/{id}` | Delete product (Requires Admin Token) |

### 📁 Categories Management
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/categories` | Retrieve all categories |
| `POST` | `/api/categories` | Create category (Requires Admin Token) |
| `DELETE` | `/api/categories/{id}` | Delete category (Requires Admin Token) |

### 📦 Orders & Sales
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/orders` | Retrieve list of orders with items |
| `PATCH` | `/api/orders/{id}/status` | Update order status (`pending`, `paid`, `completed`, `cancelled`) |

### 🛒 MiniApp Customer Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/checkout` | Submit cart items, returns transaction ID & AnajakPay KHQR |
| `GET` | `/api/order/{tx_id}/status` | Real-time payment verification polling |
| `GET` | `/api/qr-image?qr=...` | Stream PNG image generated from raw KHQR EMV payload |

### 🖼️ Media Uploads
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload` | Multipart file upload (images saved to `/static/uploads/...`) |

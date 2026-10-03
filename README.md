# 🥗 Food Fruit KH — Decoupled 3-Project Monorepo

Welcome to the decoupled **Food Fruit KH** platform! The system has been modularized into **3 standalone projects** so you can develop, deploy, and host each part on its own domain or service without coupling:

```
Food KH/
├── backend/            👉 Standalone Backend (FastAPI, SQLite, Telegram Bot, AnajakPay KHQR)
├── frontend_admin/     👉 Standalone Admin Dashboard (React.js, TailwindCSS v3, Vite)
├── frontend_miniapp/   👉 Standalone Telegram MiniApp (HTML5, Vanilla CSS, JS, Telegram WebApp SDK)
```

---

## 🏗️ 3 Independent Projects Overview

```
                      +---------------------------------------+
                      |   Telegram Client (Mobile / Desktop)  |
                      +---------------------------------------+
                                   |               |
                         Telegram Bot Polling      |
                                   |               v
                                   |      +---------------------------------+
                                   |      | frontend_miniapp/               |
                                   |      | (Telegram MiniApp Store)        |
                                   |      | Hosted on Vercel / GitHub Pages |
                                   |      +---------------------------------+
                                   |                       |
                                   v                       v (REST Calls)
  +---------------------------------------------------------------------------------+
  | backend/ (FastAPI + SQLite + Telegram Bot Worker)                               |
  | - CORS Enabled for all origins & ports                                          |
  | - Rest APIs: /api/products, /api/categories, /api/orders, /api/checkout, etc.   |
  | - AnajakPay KHQR Payment Processing & Live Polling                              |
  +---------------------------------------------------------------------------------+
                                   ^
                                   | (REST API & Token Auth)
                                   |
                  +---------------------------------+
                  | frontend_admin/                 |
                  | (React.js + TailwindCSS Admin)  |
                  | Merchant Inventory & Orders     |
                  +---------------------------------+
```

---

## 📁 1. `backend/` — FastAPI REST API & Telegram Bot
- **Technology**: Python 3, FastAPI, Uvicorn, SQLite3, `python-telegram-bot` v21, AnajakPay.
- **Port**: `8000` (or dynamic `$PORT` on Render).
- **CORS**: Fully enabled for all external domains.
- **How to Run**:
  ```bash
  cd backend
  pip install -r requirements.txt
  python bot_worker.py    # Runs both FastAPI and Bot in one process
  # Or: python main.py    # Runs only the FastAPI REST API
  ```
- **Documentation**: See [backend/README.md](file:///d:/Food%20KH/backend/README.md).

---

## 💻 2. `frontend_admin/` — React.js + TailwindCSS Dashboard
- **Technology**: React 19, TailwindCSS v3, Vite, Lucide React.
- **Port**: `5173`.
- **Key Features**:
  - Full Product CRUD with bilingual (Khmer & English) support.
  - Active stock toggle & image upload.
  - Category manager with custom emoji icons.
  - Live order monitoring with status badge filters and receipt modals.
  - Revenue analytics in USD ($) and KHR (៛).
  - Configurable Backend Host in UI Settings.
- **How to Run**:
  ```bash
  cd frontend_admin
  npm install
  npm run dev            # Development server on http://localhost:5173
  npm run build          # Production static bundle in dist/
  ```
- **Documentation**: See [frontend_admin/README.md](file:///d:/Food%20KH/frontend_admin/README.md).

---

## 📱 3. `frontend_miniapp/` — Customer Telegram MiniApp
- **Technology**: Modern HTML5, Custom CSS, Vanilla JavaScript, Telegram WebApp SDK.
- **Key Features**:
  - Anti-Inspect security (DevTools disabling, right-click protection).
  - Category filtering & instant search.
  - Slide-up cart drawer & Khmer typography.
  - KHQR EMV QR Code display & automatic 3-second payment polling.
  - Direct ABA Mobile deeplink button.
- **How to Run**:
  ```bash
  cd frontend_miniapp
  python -m http.server 5000   # Or npx serve .
  ```
- **Documentation**: See [frontend_miniapp/README.md](file:///d:/Food%20KH/frontend_miniapp/README.md).

---

## ⚡ Quick Deployment Guide

| Project | Recommended Platform | Build / Start Command | Notes |
|---|---|---|---|
| **`backend/`** | [Render](https://render.com) (Web Service) | `pip install -r backend/requirements.txt`<br>Start: `python backend/bot_worker.py` | Add Persistent Disk at `/var/data` for SQLite & images |
| **`frontend_admin/`** | [Vercel](https://vercel.com) or [Netlify](https://netlify.com) | `npm run build`<br>Output: `dist` | Set root to `frontend_admin` |
| **`frontend_miniapp/`** | [GitHub Pages](https://pages.github.com) or [Cloudflare Pages](https://pages.cloudflare.com) | Static (no build step needed) | Set URL in [@BotFather](https://t.me/botfather) Menu Button |

---

## 🔐 Default Credentials
- **Admin Username**: `admin`
- **Admin Password**: `foodkh2026`
- **Telegram Bot**: `@foodkhtestingbot`

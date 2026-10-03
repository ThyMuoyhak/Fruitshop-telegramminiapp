# Food KH — Merchant Admin Portal (React + TailwindCSS)

This directory contains the standalone **Admin Control Dashboard** for the Food KH platform. Built with **React 19**, **TailwindCSS v3**, and **Vite**, it allows store merchants to manage products, categories, orders, and review analytics independently from any domain.

---

## 🌟 Key Features

- **Modern Glassmorphic UI**: High-contrast, dark-mode design tailored for desktop and mobile merchants.
- **Full Inventory Control**: Add, edit, delete food items, toggle stock in real time, and upload photos with live previews.
- **Category Manager**: Organize menu categories with custom emoji icons and sorting indexes.
- **Orders & Live Receipts**: Filter orders by status (`pending`, `paid`, `completed`, `cancelled`), view ordered items and customer delivery information, and change order status.
- **Revenue Analytics**: Visual summary cards showing total revenue in USD ($) and KHR (៛), active orders, and product counts.
- **Configurable Backend Host**: Switch between local backend (`http://localhost:8000`) and production (`https://...onrender.com`) via UI settings or `.env` without rebuilding.

---

## 🛠️ Quick Start

### 1. Installation

```bash
cd frontend_admin
npm install
```

### 2. Configure Backend API URL (Optional)

Create a `.env` file in `frontend_admin/` (or `.env.local`):

```ini
VITE_API_URL=http://localhost:8000
```

> **Note**: You can also configure or change the API URL directly inside the Dashboard Settings tab or on the Login screen!

### 3. Run Development Server

```bash
npm run dev
```

The admin portal will open at `http://localhost:5173`.

### 4. Build for Production

```bash
npm run build
```

The optimized static build will be generated in `dist/`.

---

## 🌐 Deploying to Vercel / Netlify / Render

### Vercel:
```bash
npx vercel
```
- **Framework Preset**: Vite
- **Root Directory**: `frontend_admin`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### Netlify:
- **Base directory**: `frontend_admin`
- **Build command**: `npm run build`
- **Publish directory**: `dist`

# Food KH — Telegram MiniApp Frontend

This directory contains the standalone **Customer Telegram MiniApp** client for the Food KH platform. It is lightweight, ultra-fast, and can be hosted on any static hosting platform (GitHub Pages, Vercel, Cloudflare Pages, Netlify, or Render Static Site).

---

## 🌟 Key Capabilities

1. **Telegram WebApp SDK Integration**: Seamlessly integrates with the Telegram client, supports haptic feedback, safe area insets, and user metadata auto-population.
2. **Anti-Inspect Security**: Protects your shop code with right-click disabling, keyboard shortcut protection (F12, Ctrl+Shift+I, etc.), and devtools defense.
3. **KHQR & ABA Pay Real-Time Polling**: Generates Bakong KHQR QR codes via AnajakPay and polls the backend every 3 seconds for instant payment confirmation without page reloads.
4. **Bilingual Support**: Fully localized in **Khmer (ភាសាខ្មែរ)** and **English** with proper typography (`Kantumruy Pro` and `Plus Jakarta Sans`).
5. **Decoupled Backend Connection**: Automatically connects to the backend API specified in `config.js` or via `?api=https://your-backend.com` URL query parameter.

---

## 🚀 Running Locally

You can serve this folder using any static HTTP server:

```bash
# Option 1: Python HTTP Server
python -m http.server 5000

# Option 2: Node.js Serve
npx serve .
```

Open `http://localhost:5000` in your browser.

---

## 🌐 Deploying to Hosting Platforms

### A. GitHub Pages
1. Push this directory or repo to GitHub.
2. In Repository Settings -> Pages, select the branch and the `/frontend_miniapp` folder.
3. Your MiniApp URL will be: `https://<username>.github.io/<repo>/`

### B. Vercel / Cloudflare Pages / Netlify
1. Connect your repository.
2. Set the **Root Directory** to `frontend_miniapp`.
3. Build Command: (Leave empty)
4. Output Directory: `.`
5. Click **Deploy**.

---

## 🤖 Linking to Telegram Bot via @BotFather

1. Open Telegram and search for [@BotFather](https://t.me/botfather).
2. Send `/mybots` and choose your bot (`@foodkhtestingbot`).
3. Select **Bot Settings** -> **Menu Button** -> **Configure menu button**.
4. Send your hosted MiniApp URL (e.g. `https://your-app.vercel.app`).
5. Set the title to: `🛍️ Open Store (ហាងទំនិញ)`.
6. Now, users opening your bot will see the Menu button that launches this MiniApp directly inside Telegram!

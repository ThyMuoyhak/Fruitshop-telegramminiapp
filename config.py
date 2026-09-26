import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "8834918127:AAGk6IK-SP_17chGe7b47IqVNob1ZftX_YM")
BOT_USERNAME = os.getenv("BOT_USERNAME", "foodkhtestingbot")

# Admin IDs (Owner: Thy Muoyhak - 1667587449)
raw_admin_ids = os.getenv("ADMIN_IDS", "1667587449")
ADMIN_IDS = [int(x.strip()) for x in raw_admin_ids.split(",") if x.strip().isdigit()]

# AnajakPay / KHQRcc (ABA Pay) Gateway Configuration
GATEWAY_PROFILE_ID = os.getenv("GATEWAY_PROFILE_ID", "OZqxhAZPSCRXBipqVZD3YVZHGURqUd9V")
GATEWAY_SECRET_KEY = os.getenv("GATEWAY_SECRET_KEY", "zXRidJXLRyQ09PWBUHR6OHsWgTeEvn1u")

# Gateway API Endpoints
ANAJAKPAY_QR_API_URL = f"https://anajakpay.com/api/{GATEWAY_PROFILE_ID}/payment-gateway/v1/payments/qr-api-khqrcc"
ANAJAKPAY_CHECK_URL = f"https://anajakpay.com/api/{GATEWAY_PROFILE_ID}/payment-gateway/v1/payments/check-transv2-khqrcc"
CHECKOUT_FRONTEND_URL = f"https://checkout.anajakpay.com/payment/khqrcc/{GATEWAY_PROFILE_ID}"
SUCCESS_CALLBACK_URL = os.getenv("SUCCESS_CALLBACK_URL", "https://anajakpay.com/dashboard")

# Store Configuration
STORE_NAME_EN = "Food Fruit KH"
STORE_NAME_KH = "ផ្លែឈើ & អាហារខ្មែរ"
STORE_CONTACT_USERNAME = os.getenv("STORE_CONTACT_USERNAME", "thymuoyhak")
SUPPORT_PHONE = os.getenv("SUPPORT_PHONE", "+855 12 345 678")

# Currency & Exchange Rate (1 USD = 4100 KHR)
KHR_EXCHANGE_RATE = int(os.getenv("KHR_EXCHANGE_RATE", "4100"))

# Database Path
DB_PATH = os.getenv("DB_PATH", "food_kh.db")

# Payment Polling Settings
POLL_INTERVAL_SECONDS = 4
MAX_POLL_ATTEMPTS = 45  # 45 * 4 = 180 seconds (3 minutes)

# Web & Telegram MiniApp Server Settings
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))

render_url = os.getenv("RENDER_EXTERNAL_URL")
if render_url:
    WEBAPP_URL = os.getenv("WEBAPP_URL", f"{render_url.rstrip('/')}/shop")
else:
    WEBAPP_URL = os.getenv("WEBAPP_URL", "http://localhost:8000/shop")

# Admin Dashboard Credentials (FastAPI MVT)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "foodkh2026")
SECRET_SESSION_KEY = os.getenv("SECRET_SESSION_KEY", "foodkh_super_secret_session_key_2026")
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")


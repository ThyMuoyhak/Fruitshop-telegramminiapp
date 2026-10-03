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

# Persistent Data Directory (supports Render Disk e.g. /var/data or local storage)
DATA_DIR = os.getenv("DATA_DIR")
if not DATA_DIR:
    if os.path.exists("/var/data"):
        DATA_DIR = "/var/data"
    elif os.path.exists("/data"):
        DATA_DIR = "/data"
    else:
        DATA_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception as e:
    print(f"⚠️ Failed to create DATA_DIR {DATA_DIR}: {e}. Falling back to local dir.")
    DATA_DIR = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(DATA_DIR, exist_ok=True)

# Database Path (ALWAYS stored inside DATA_DIR on persistent disk)
raw_db_path = os.getenv("DB_PATH")
if raw_db_path:
    # If DB_PATH is just a filename like "food_kh.db" or relative path, force it into DATA_DIR
    if not os.path.isabs(raw_db_path) or not raw_db_path.startswith(DATA_DIR):
        db_filename = os.path.basename(raw_db_path) or "food_kh.db"
        DB_PATH = os.path.join(DATA_DIR, db_filename)
    else:
        DB_PATH = raw_db_path
else:
    DB_PATH = os.path.join(DATA_DIR, "food_kh.db")

DB_PATH = os.path.abspath(DB_PATH)

# Upload Directory (ALWAYS stored inside DATA_DIR on persistent disk)
raw_upload_dir = os.getenv("UPLOAD_DIR")
if raw_upload_dir:
    if not os.path.isabs(raw_upload_dir) or not raw_upload_dir.startswith(DATA_DIR):
        upload_sub = os.path.basename(raw_upload_dir) or "uploads"
        UPLOAD_DIR = os.path.join(DATA_DIR, upload_sub)
    else:
        UPLOAD_DIR = raw_upload_dir
else:
    UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)

try:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception as e:
    print(f"⚠️ Failed to create UPLOAD_DIR {UPLOAD_DIR}: {e}")

# Storage diagnostics print on startup
print("=" * 60)
print("💾 Food KH Storage & Disk Configuration:")
print(f"  • DATA_DIR   : {DATA_DIR}")
print(f"  • DB_PATH    : {DB_PATH}")
print(f"  • UPLOAD_DIR : {UPLOAD_DIR}")
is_disk_active = (os.path.exists("/var/data") or (os.getenv("DATA_DIR") and os.getenv("DATA_DIR").startswith("/var/data"))) and DB_PATH.startswith(DATA_DIR)
if is_disk_active:
    print("  • Status     : 🟢 PERSISTENT DISK DETECTED & ACTIVE (/var/data)")
    print("  • Note       : SQLite DB & uploads are stored safely on the persistent disk.")
else:
    print("  • Status     : ⚠️ EPHEMERAL STORAGE (Container Local)")
    print("  • WARNING    : Any data created WILL BE CLEARED on redeployment!")
    print("  • ACTION REQ : In Render Dashboard > Disks, set Mount Path to: /var/data")
    print("                 In Render Dashboard > Environment, set DATA_DIR to: /var/data")
print("=" * 60)

# If persistent DB does not exist yet on a fresh disk, copy initial seed DB if available
if not os.path.exists(DB_PATH):
    possible_seeds = [
        os.path.join(os.getcwd(), "food_kh.db"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "food_kh.db"),
    ]
    for seed in possible_seeds:
        if os.path.exists(seed) and os.path.abspath(seed) != os.path.abspath(DB_PATH):
            try:
                import shutil
                shutil.copy2(seed, DB_PATH)
                print(f"✅ Initialized persistent database from seed: {seed} -> {DB_PATH}")
                break
            except Exception as e:
                print(f"Could not copy seed DB: {e}")

# If persistent uploads directory is empty, seed with initial sample images if available
repo_uploads = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
if os.path.exists(repo_uploads) and os.path.abspath(UPLOAD_DIR) != os.path.abspath(repo_uploads):
    try:
        import shutil
        for f in os.listdir(repo_uploads):
            src = os.path.join(repo_uploads, f)
            dst = os.path.join(UPLOAD_DIR, f)
            if os.path.isfile(src) and not os.path.exists(dst):
                shutil.copy2(src, dst)
    except Exception:
        pass

# Payment Polling Settings
POLL_INTERVAL_SECONDS = 4
MAX_POLL_ATTEMPTS = 45  # 45 * 4 = 180 seconds (3 minutes)

# Web & Telegram MiniApp Server Settings
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8000")))

# MiniApp URL (Hosted on Netlify)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://cute-blini-a8e17a.netlify.app")

# Admin Dashboard Frontend URL (Hosted on Netlify)
ADMIN_FRONTEND_URL = os.getenv("ADMIN_FRONTEND_URL", "https://delightful-tulumba-57fd5b.netlify.app")

# Admin Dashboard Credentials (FastAPI MVT)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "foodkh2026")
SECRET_SESSION_KEY = os.getenv("SECRET_SESSION_KEY", "foodkh_super_secret_session_key_2026")


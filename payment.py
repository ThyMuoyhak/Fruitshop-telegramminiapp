import hashlib
import io
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import qrcode
from qrcode.image.pil import PilImage

import config
import database

logger = logging.getLogger(__name__)

def generate_create_hash(transaction_id: str, amount: str, success_url: str, remark: str) -> str:
    """
    Formula: sha1(secret + transaction_id + amount + success_url + remark)
    """
    raw_str = f"{config.GATEWAY_SECRET_KEY}{transaction_id}{amount}{success_url}{remark}"
    return hashlib.sha1(raw_str.encode("utf-8")).hexdigest()

def generate_check_hash(transaction_id: str) -> str:
    """
    Formula: sha1(secret + transaction_id)
    """
    raw_str = f"{config.GATEWAY_SECRET_KEY}{transaction_id}"
    return hashlib.sha1(raw_str.encode("utf-8")).hexdigest()

async def create_khqr_payment(transaction_id: str, amount: float, remark: str = "Food Fruit KH") -> Dict[str, Any]:
    """
    Calls AnajakPay Direct QR API (qr-api-khqrcc) to generate a KHQR code for ABA Pay / Bakong
    """
    amount_str = f"{amount:.2f}"
    success_url = config.SUCCESS_CALLBACK_URL
    sign_hash = generate_create_hash(transaction_id, amount_str, success_url, remark)

    payload = {
        "transaction_id": transaction_id,
        "amount": amount_str,
        "success_url": success_url,
        "remark": remark,
        "hash": sign_hash
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(config.ANAJAKPAY_QR_API_URL, data=payload)
            data = resp.json()

            if resp.status_code == 200 and data.get("responseCode") == 0:
                payment_data = data.get("data", {})
                qr_code = payment_data.get("qr", "")
                qr_url = payment_data.get("qr_url", "")
                md5_val = payment_data.get("md5", "")

                # Update order in DB
                database.update_order_payment_info(transaction_id, qr_code, qr_url, md5_val)

                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "amount": amount_str,
                    "qr": qr_code,
                    "qr_url": qr_url,
                    "md5": md5_val,
                    "raw": payment_data
                }
            else:
                logger.error(f"Failed to create KHQR payment: {data}")
                return {
                    "success": False,
                    "error": data.get("responseMessage", "Unknown payment gateway error")
                }
    except Exception as e:
        logger.exception(f"Exception during create_khqr_payment: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def check_transaction_status(transaction_id: str) -> Dict[str, Any]:
    """
    Polls AnajakPay Check Transaction V2 (check-transv2-khqrcc)
    """
    sign_hash = generate_check_hash(transaction_id)
    payload = {
        "transaction_id": transaction_id,
        "hash": sign_hash
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(config.ANAJAKPAY_CHECK_URL, data=payload)
            data = resp.json()

            if resp.status_code == 200 and data.get("responseCode") == 0:
                res_data = data.get("data", {})
                status = res_data.get("status", "pending").lower()
                paid_amount = res_data.get("amount")

                if status == "success":
                    # Mark order as PAID in DB
                    now_str = datetime.now().isoformat()
                    database.update_order_status(transaction_id, "PAID", paid_at=now_str)

                return {
                    "success": True,
                    "status": status,
                    "amount": paid_amount,
                    "data": res_data
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "error": data.get("responseMessage", "Verification request failed")
                }
    except Exception as e:
        logger.exception(f"Error checking transaction status: {e}")
        return {
            "success": False,
            "status": "error",
            "error": str(e)
        }

def generate_local_qr_bytes(qr_string: str) -> io.BytesIO:
    """
    Generates a high-quality QR code image in memory as BytesIO for Telegram photo upload.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

async def poll_payment_background(application, transaction_id: str, user_id: int, order_id: int):
    """
    Background polling worker that checks status every POLL_INTERVAL_SECONDS for MAX_POLL_ATTEMPTS.
    If paid, updates database and notifies customer & admins.
    """
    logger.info(f"Starting payment poller for order #{order_id} (TX: {transaction_id})")

    for attempt in range(config.MAX_POLL_ATTEMPTS):
        await asyncio.sleep(config.POLL_INTERVAL_SECONDS)

        # Check if already paid or cancelled in database first
        order = database.get_order_by_tx(transaction_id)
        if not order:
            break
        if order["status"] in ["PAID", "PROCESSING", "DELIVERING", "COMPLETED", "CANCELLED"]:
            if order["status"] != "PENDING":
                logger.info(f"Order #{order_id} is already {order['status']}, stopping poller.")
                return

        result = await check_transaction_status(transaction_id)
        if result.get("success") and result.get("status") == "success":
            logger.info(f"Payment SUCCESS confirmed for order #{order_id} (TX: {transaction_id})")

            # Notify user
            paid_amount = result.get("amount") or order["total_amount"]
            khr_amount = int(float(paid_amount) * config.KHR_EXCHANGE_RATE)

            user_msg = (
                f"🎉 <b>ការទូទាត់ប្រាក់បានជោគជ័យ! / Payment Successful!</b>\n\n"
                f"✅ <b>វិក្កយបត្រ / Order ID:</b> #{order_id} (<code>{transaction_id}</code>)\n"
                f"💵 <b>ចំនួនទឹកប្រាក់ / Amount Paid:</b> ${float(paid_amount):.2f} (~ {khr_amount:,} ៛)\n"
                f"🏦 <b>វិធីទូទាត់ / Payment Method:</b> ABA Pay / KHQR\n"
                f"👤 <b>អ្នកទទួល / Customer:</b> {order['delivery_name']}\n"
                f"📱 <b>លេខទូរស័ព្ទ / Phone:</b> {order['delivery_phone']}\n"
                f"📍 <b>ទីតាំងដឹកជញ្ជូន / Address:</b> {order['delivery_address']}\n\n"
                f"👨‍🍳 ហាងកំពុងរៀបចំការវេចខ្ចប់ និងដឹកជញ្ជូនជូនលោកអ្នកយ៉ាងយកចិត្តទុកដាក់!\n"
                f"Our team is now preparing your fresh order for delivery. Thank you!"
            )

            try:
                await application.bot.send_message(
                    chat_id=user_id,
                    text=user_msg,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to send payment confirmation to user {user_id}: {e}")

            # Notify Admins
            admin_msg = (
                f"🚨 <b>ការបញ្ជាទិញថ្មីត្រូវបានទូទាត់ប្រាក់រួចរាល់! / NEW PAID ORDER!</b>\n\n"
                f"📦 <b>Order ID:</b> #{order_id}\n"
                f"🔖 <b>Transaction ID:</b> <code>{transaction_id}</code>\n"
                f"💰 <b>Total Paid:</b> ${float(paid_amount):.2f}\n"
                f"👤 <b>Customer:</b> {order['delivery_name']}\n"
                f"📞 <b>Phone:</b> {order['delivery_phone']}\n"
                f"📍 <b>Delivery Address:</b> {order['delivery_address']}\n"
                f"📝 <b>Note:</b> {order.get('delivery_note') or 'None'}\n\n"
                f"🛒 <b>Items:</b>\n"
            )
            for item in order.get("items", []):
                admin_msg += f" • {item['product_name']} x {item['quantity']} ({item['unit']}) = ${item['subtotal']:.2f}\n"

            for admin_id in config.ADMIN_IDS:
                try:
                    await application.bot.send_message(
                        chat_id=admin_id,
                        text=admin_msg,
                        parse_mode="HTML"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin {admin_id}: {e}")

            return

    logger.info(f"Payment polling finished for TX: {transaction_id} (attempts reached)")

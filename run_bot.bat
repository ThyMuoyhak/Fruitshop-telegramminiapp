@echo off
chcp 65001 > nul
title Food Fruit KH - Telegram Bot
color 0A
echo ===================================================
echo     Starting Food Fruit KH Platform
echo     - Telegram MiniApp: http://localhost:8000/shop
echo     - Admin Dashboard: http://localhost:8000/admin
echo     - Telegram Bot: @foodkhtestingbot
echo     - Payment Gateway: ABA Pay / KHQR (AnajakPay)
echo ===================================================
echo.
python run_all.py
pause

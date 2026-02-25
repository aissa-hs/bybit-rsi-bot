@echo off
title RSI Bot
cd /d "%~dp0"
echo ========================================
echo    RSI Trading Bot - Starting...
echo ========================================
echo.
python bybit_rsi_bot.py
pause

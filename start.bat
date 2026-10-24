@echo off
chcp 65001 >nul
title Go Absent - He Thong Quan Ly Nghi Phep Telegram Bot
echo ===================================================
echo       GO ABSENT - TELEGRAM BOT & WEB DASHBOARD
echo ===================================================
echo.

:: 1. Kiem tra Python tren may tinh
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [LOI] Khong tim thay Python tren may tinh cua ban!
    echo Vui long cai dat Python va tick vao muc "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: 2. Kiem tra file cau hinh .env
if not exist ".env" (
    echo [THONG BAO] Chua co file .env, he thong se tao tu .env.example...
    copy .env.example .env >nul
    echo Da tao file .env. Vui long mo file .env va dien BOT_TOKEN cua ban!
    echo.
    pause
    exit /b 1
)

:: 3. Kiem tra va cai dat thu vien
echo [*] Dang kiem tra va cai dat thu vien phu thuoc...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [CANH BAO] Khong the tu dong cai dat thu vien qua pip. Dang thu khoi dong he thong...
)

:: 4. Doc cong WEB_PORT tu file cau hinh (mac dinh 5000)
set WEB_PORT=5000
for /f "tokens=*" %%i in ('python -c "from config import WEB_PORT; print(WEB_PORT)" 2^>nul') do (
    set WEB_PORT=%%i
)

:: 5. Kiem tra va khoi chay Ngrok Tunnel
set NGROK_CMD=
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    set NGROK_CMD=ngrok
) else if exist "ngrok.exe" (
    set NGROK_CMD=ngrok.exe
)

if defined NGROK_CMD goto RUN_NGROK

echo.
echo ---------------------------------------------------
echo [THONG BAO] May ban chua co cong cu Ngrok (tao Webhook).
echo ---------------------------------------------------
echo Ban co muon he thong TU DONG TAI Ngrok ve may khong?
echo   [1] Co    - Tu dong tai ve chay ngay (Khuyen dung)
echo   [2] Khong - Bo qua, chay bot o che do Polling mac dinh
echo.
set NGROK_CHOICE=1
set /p NGROK_CHOICE="Lua chon cua ban [1/2] (Nhan Enter de mac dinh chon 1): "

if "%NGROK_CHOICE%"=="2" goto SKIP_NGROK
if /i "%NGROK_CHOICE%"=="N" goto SKIP_NGROK
if /i "%NGROK_CHOICE%"=="no" goto SKIP_NGROK

echo.
echo [*] Dang tu dong tai Ngrok ve thu muc du an, vui long cho...
curl.exe -L -# -o ngrok.zip "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip" 2>nul
if not exist "ngrok.zip" (
    powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object Net.WebClient).DownloadFile('https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip', 'ngrok.zip')"
)
tar.exe -xf ngrok.zip 2>nul
if not exist "ngrok.exe" (
    powershell -Command "Expand-Archive -Path 'ngrok.zip' -DestinationPath '.' -Force"
)
if exist "ngrok.zip" del ngrok.zip

if exist "ngrok.exe" (
    set NGROK_CMD=ngrok.exe
    echo [THANH CONG] Da tai xong Ngrok!
    goto RUN_NGROK
) else (
    echo [CANH BAO] Khong the tai Ngrok. He thong se chay che do Polling.
    goto SKIP_NGROK
)

:RUN_NGROK
echo [*] Tim thay Ngrok! Dang tu dong mo Ngrok Tunnel tren port %WEB_PORT%...
start "Ngrok Tunnel - Port %WEB_PORT%" %NGROK_CMD% http %WEB_PORT%
goto APP_START

:SKIP_NGROK
echo [i] He thong dang chay che do Long-Polling mac dinh.

:APP_START
echo.
echo [*] Dang khoi dong ung dung Go Absent...
echo [!] Dashboard Web: http://localhost:%WEB_PORT%
echo.

:: 6. Khoi chay may chu ung dung Python
python app.py

if %errorlevel% neq 0 (
    echo.
    echo [THONG BAO] Ung dung da dung lai.
    pause
)

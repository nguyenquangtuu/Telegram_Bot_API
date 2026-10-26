@echo off
setlocal enabledelayedexpansion
title Go Absent - He Thong Quan Ly Nghi Phep Telegram Bot
echo ===================================================
echo       GO ABSENT - TELEGRAM BOT ^& WEB DASHBOARD
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
    echo [CANH BAO] Khong the tu dong cai dat thu vien qua pip. Dang thu tiep tuc...
)

:: 4. Doc cong WEB_PORT tu file cau hinh (mac dinh 5000)
set WEB_PORT=5000
for /f "tokens=*" %%i in ('python -c "import config; print(config.WEB_PORT)" 2^>nul') do (
    set WEB_PORT=%%i
)

:: 5. Menu lua chon co che chay
echo.
echo ===================================================
echo        CHON CO CHE KET NOI TELEGRAM BOT
echo ===================================================
echo.
echo   [1] Chay tren Localhost (Dung GetUpdates lay su kien moi)
echo       - Nhan tin nhan truc tiep qua Telegram Long-Polling.
echo       - Khong can Internet domain, khong can Ngrok.
echo       - Cau hinh Webhook tren Web Dashboard se bi vo hieu hoa.
echo.
echo   [2] Mo NGROK (Nhan Webhook)
echo       - Tu dong mo duong ham HTTPS Ngrok toi may tinh.
echo       - Telegram se day su kien truc tiep qua Webhook endpoint.
echo       - Cho phep xem, bat/tat va cau hinh Webhook tren Dashboard.
echo.
set USER_MODE=1
set /p USER_MODE="Nhap lua chon cua ban [1/2] (Nhan Enter mac dinh la 1): "

if "%USER_MODE%"=="2" goto MODE_NGROK
if /i "%USER_MODE%"=="webhook" goto MODE_NGROK

:MODE_LOCALHOST
echo.
echo ---------------------------------------------------
echo [*] BAN DA CHON: [1] Chay tren LOCALHOST (GetUpdates)
echo [*] He thong se nhan su kien moi qua Long-Polling.
echo [*] Webhook tren Dashboard se bi khoa.
echo ---------------------------------------------------
set BOT_MODE=polling
goto RUN_APP

:MODE_NGROK
echo.
echo ---------------------------------------------------
echo [*] BAN DA CHON: [2] Mo NGROK (Nhan Webhook)
echo ---------------------------------------------------

:: Kiem tra cong cu Ngrok
set NGROK_CMD=
where ngrok >nul 2>&1
if %errorlevel% equ 0 (
    set NGROK_CMD=ngrok
) else if exist "ngrok.exe" (
    set NGROK_CMD=ngrok.exe
)

if defined NGROK_CMD goto LAUNCH_NGROK

echo [THONG BAO] Chua tim thay file ngrok.exe tren may cua ban.
echo Ban co muon he thong TU DONG TAI Ngrok ve may khong?
echo   [1] Co    - Tu dong tai ve chay ngay (Khuyen dung)
echo   [2] Khong - Chuyen ve chay tren Localhost (GetUpdates)
echo.
set DL_CHOICE=1
set /p DL_CHOICE="Lua chon cua ban [1/2] (Nhan Enter mac dinh la 1): "

if "%DL_CHOICE%"=="2" goto FALLBACK_POLLING
if /i "%DL_CHOICE%"=="N" goto FALLBACK_POLLING

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
    goto LAUNCH_NGROK
) else (
    echo [CANH BAO] Khong the tai Ngrok ve may. Chuyen ve che do Localhost (GetUpdates)...
    goto FALLBACK_POLLING
)

:LAUNCH_NGROK
echo [*] Dang mo Ngrok Tunnel tren cong %WEB_PORT%...
start "Ngrok Tunnel - Port %WEB_PORT%" %NGROK_CMD% http %WEB_PORT%
echo [*] Dang cho 3 giay de Ngrok khoi tao duong ham HTTPS...
timeout /t 3 /nobreak >nul 2>&1
set BOT_MODE=webhook
goto RUN_APP

:FALLBACK_POLLING
set BOT_MODE=polling
echo [i] He thong tu dong chuyen sang che do Localhost (GetUpdates).
goto RUN_APP

:RUN_APP
echo.
echo [*] Dang khoi dong may chu Go Absent...
echo [!] Dashboard Web: http://localhost:%WEB_PORT%
echo.

:: 6. Khoi chay may chu ung dung Python voi BOT_MODE da chon
python app.py --mode=%BOT_MODE%

if %errorlevel% neq 0 (
    echo.
    echo [THONG BAO] Ung dung da dung lai.
    pause
)

@echo off
TITLE ERP BOT - SETUP (STABLE VERSION)
CLS

echo ========================================================
echo      🤖 ERP BOT - INSTALLER (PYTHON + TESSERACT)
echo ========================================================
echo.

:: 1. CEK ADMINISTRATOR (Cara Paling Aman)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [STATUS] ✅ Akses Administrator DITERIMA. Lanjut...
) else (
    echo [STATUS] ❌ AKSES DITOLAK!
    echo.
    echo ⚠️  Script ini butuh izin install program.
    echo ⚠️  Tolong tutup jendela ini, lalu:
    echo     KLIK KANAN file ini -^> Pilih "Run as Administrator"
    echo.
    pause
    exit
)

:: ---------------------------------------------------------
:: 2. PINDAH KE FOLDER SCRIPT (Penting biar ga nyasar)
:: ---------------------------------------------------------
cd /d "%~dp0"

:: ---------------------------------------------------------
:: 3. CEK & INSTALL PYTHON
:: ---------------------------------------------------------
echo.
echo [1/4] Mengecek Python...
python --version >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo    ✅ Python sudah terinstall.
) ELSE (
    echo    ⚠️ Python tidak ditemukan! Sedang mendownload Python 3.11...
    
    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe -OutFile python_installer.exe"
    
    echo    ⚙️ Menginstall Python (Tunggu sebentar)...
    python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    del python_installer.exe
    echo    ✅ Python berhasil diinstall!
    
    :: Refresh Path sementara
    set "PATH=%PATH%;C:\Program Files\Python311\Scripts\;C:\Program Files\Python311\"
)

:: ---------------------------------------------------------
:: 4. CEK & INSTALL TESSERACT OCR
:: ---------------------------------------------------------
echo.
echo [2/4] Mengecek Tesseract OCR...
if exist "C:\Program Files\Tesseract-OCR\tesseract.exe" (
    echo    ✅ Tesseract sudah terinstall.
) ELSE (
    echo    ⚠️ Tesseract tidak ditemukan! Sedang mendownload...
    
    powershell -Command "Invoke-WebRequest https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe -OutFile tesseract_installer.exe"
    
    echo    ⚙️ Menginstall Tesseract (Tunggu sebentar)...
    tesseract_installer.exe /S
    
    del tesseract_installer.exe
    echo    ✅ Tesseract berhasil diinstall!
)

:: ---------------------------------------------------------
:: 5. SETUP VIRTUAL ENVIRONMENT
:: ---------------------------------------------------------
echo.
echo [3/4] Setup Project Environment...
if not exist "venv" (
    echo    📦 Membuat folder venv...
    python -m venv venv
) else (
    echo    ✅ Folder venv sudah ada.
)

:: ---------------------------------------------------------
:: 6. INSTALL REQUIREMENTS
:: ---------------------------------------------------------
echo.
echo [4/4] Install Library Bot...
call venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ========================================================
echo 🎉 SETUP SELESAI! SEMUA SIAP TEMPUR.
echo ========================================================
echo.
pause

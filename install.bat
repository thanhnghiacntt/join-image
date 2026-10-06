@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ============================================
echo   Cai dat moi truong cho cong cu ghep anh
echo ============================================

REM --- Tim Python (uu tien Python Launcher "py") ---
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo [LOI] Khong tim thay Python. Hay cai Python 3.9+ tu https://www.python.org/downloads/
    echo       Nho tick "Add python.exe to PATH" khi cai.
    pause
    exit /b 1
)
%PY% --version

REM --- Tao moi truong ao rieng .venv ---
if exist ".venv\Scripts\python.exe" (
    echo Moi truong .venv da ton tai, bo qua buoc tao.
) else (
    echo Dang tao moi truong ao .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [LOI] Khong tao duoc moi truong ao.
        pause
        exit /b 1
    )
)

REM --- Cai thu vien ---
echo Dang cai thu vien ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [LOI] Cai thu vien that bai. Kiem tra ket noi mang.
    pause
    exit /b 1
)

REM --- Kiem tra ---
".venv\Scripts\python.exe" -c "import cv2, numpy; print('OpenCV', cv2.__version__, '| NumPy', numpy.__version__)"

echo.
echo Cai dat xong! Cach dung:
echo   stitch.bat D:\thu_muc_anh
echo   (hoac keo tha thu muc anh vao file stitch.bat)
echo.
pause

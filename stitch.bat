@echo off
chcp 65001 >nul
setlocal
set "HERE=%~dp0"

if not exist "%HERE%.venv\Scripts\python.exe" (
    echo [LOI] Chua cai dat. Hay chay install.bat truoc.
    pause
    exit /b 1
)

if "%~1"=="" (
    "%HERE%.venv\Scripts\python.exe" "%HERE%stitch.py" --help
    echo.
    echo Vi du: stitch.bat D:\thu_muc_anh
    pause
    exit /b 0
)

"%HERE%.venv\Scripts\python.exe" "%HERE%stitch.py" %*
set "RC=%ERRORLEVEL%"

REM Neu duoc mo bang keo-tha (khong co cua so cmd), giu man hinh de doc ket qua
echo %CMDCMDLINE% | find /i "%~0" >nul && pause
exit /b %RC%

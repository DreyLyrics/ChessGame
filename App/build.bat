@echo off
chcp 65001 >nul
title ChessGamePlay — Build EXE

set PY=C:\Users\datla\AppData\Local\Programs\Python\Python312\python.exe
set ROOT=%~dp0..
set ENTRY=%ROOT%\UI\menu.py
set DIST=%ROOT%\App\dist
set WORK=%ROOT%\App\build_tmp
set NAME=ChessGamePlay

echo.
echo ============================================
echo   ChessGamePlay — PyInstaller Build
echo ============================================
echo.

echo [*] Kiem tra PyInstaller...
%PY% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [*] Cai PyInstaller...
    %PY% -m pip install pyinstaller
)

echo [*] Kiem tra thu vien...
%PY% -m pip install pygame flask flask-socketio eventlet --quiet

echo.
echo [*] Bat dau build...
echo     Entry : %ENTRY%
echo     Output: %DIST%\%NAME%
echo.

%PY% -m PyInstaller ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --name "%NAME%" ^
    --distpath "%DIST%" ^
    --workpath "%WORK%" ^
    --specpath "%ROOT%\App" ^
    --add-data "%ROOT%\assets;assets" ^
    --add-data "%ROOT%\DataBase;DataBase" ^
    --add-data "%ROOT%\stockfish;stockfish" ^
    --add-data "%ROOT%\src;src" ^
    --add-data "%ROOT%\UI;UI" ^
    --add-data "%ROOT%\Bot;Bot" ^
    --add-data "%ROOT%\LocalBattle;LocalBattle" ^
    --add-data "%ROOT%\Online;Online" ^
    --hidden-import pygame ^
    --hidden-import flask ^
    --hidden-import flask_socketio ^
    --hidden-import engineio ^
    --hidden-import socketio ^
    --hidden-import eventlet ^
    --hidden-import tkinter ^
    --hidden-import sqlite3 ^
    --hidden-import engineio.async_drivers.threading ^
    "%ENTRY%"

if errorlevel 1 (
    echo.
    echo [X] Build THAT BAI!
    pause
    exit /b 1
)

echo.
echo [*] Don dep file tam...
if exist "%WORK%" rmdir /s /q "%WORK%"

echo.
echo ============================================
echo   BUILD THANH CONG!
echo   Output: %DIST%\%NAME%\%NAME%.exe
echo ============================================
echo.
pause >nul
explorer "%DIST%\%NAME%"

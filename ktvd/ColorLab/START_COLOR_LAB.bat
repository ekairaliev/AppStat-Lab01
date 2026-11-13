@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Starting COLOR LAB...
py -m marimo run photo_app.py
if errorlevel 1 (
  echo.
  echo Try INSTALL_LIBRARIES.bat first, then run again.
  pause
)

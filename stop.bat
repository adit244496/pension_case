@echo off
REM Closes copies of this app left running from earlier sessions, so that
REM start.bat can use the usual ports again.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0deploy\stop.ps1"
echo.
echo Run start.bat to launch a fresh copy.

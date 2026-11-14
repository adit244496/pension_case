@echo off
REM Launches the API and the web interface, then opens the browser.
setlocal EnableDelayedExpansion
cd /d "%~dp0"

if not exist backend\.venv (
  echo Run setup.bat first.
  exit /b 1
)

REM setup.bat unpacks a private Node here when the system one is missing or
REM too old; put it first so both windows below use it.
if exist "%LOCALAPPDATA%\Programs\nodejs22\node.exe" set "PATH=%LOCALAPPDATA%\Programs\nodejs22;%PATH%"
node -e "var v=process.versions.node.split('.').map(Number);process.exit(v[0]>22||(v[0]===22&&v[1]>=13)?0:1)" >nul 2>&1
if errorlevel 1 (
  echo Node.js 22.13 or newer is needed. Run setup.bat to install it.
  pause
  exit /b 1
)

REM Pick the first free API port from 8000 upward, in case one is still in use.
set API_PORT=
for %%P in (8000 8001 8002 8003) do (
  if not defined API_PORT (
    netstat -ano | findstr /R /C:":%%P .*LISTENING" >nul 2>&1
    if errorlevel 1 set API_PORT=%%P
  )
)
if not defined API_PORT (
  echo Could not find a free port between 8000 and 8003. Run stop.bat first.
  exit /b 1
)

REM And the same for the web port. This one is passed to Vite rather than left
REM to it: Vite quietly moves to the next free port when 5173 is taken, and the
REM browser then opens an older copy of the app that is still running.
set WEB_PORT=
for %%P in (5173 5174 5175 5176) do (
  if not defined WEB_PORT (
    netstat -ano | findstr /R /C:":%%P .*LISTENING" >nul 2>&1
    if errorlevel 1 set WEB_PORT=%%P
  )
)
if not defined WEB_PORT (
  echo Could not find a free port between 5173 and 5176. Run stop.bat first.
  exit /b 1
)

set STALE=
if not "%API_PORT%"=="8000" set STALE=1
if not "%WEB_PORT%"=="5173" set STALE=1
if not defined STALE goto :launch

echo.
echo NOTE: an earlier copy of the app is still running and holding the usual
echo       ports, so this one is starting on %WEB_PORT% / %API_PORT% instead.
echo       Run stop.bat to close the old one if you do not want two copies.
echo.

:launch
echo Starting API on port %API_PORT% ...
REM PENSION_LOCAL_MODE skips the sign-in screen for this desktop run. The API
REM still only trusts it for requests from this machine (127.0.0.1).
start "Pension API" cmd /k "cd /d %~dp0backend && set PENSION_LOCAL_MODE=1&& .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %API_PORT%"
start "Pension Web" cmd /k "cd /d %~dp0frontend && set PENSION_API=http://127.0.0.1:%API_PORT%&& set PENSION_WEB_PORT=%WEB_PORT%&& npm run dev"

timeout /t 6 /nobreak >nul
start http://localhost:%WEB_PORT%

echo.
echo API : http://127.0.0.1:%API_PORT%/docs
echo Web : http://localhost:%WEB_PORT%
echo Close the two console windows to stop the application.

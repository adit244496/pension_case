@echo off
REM One-time setup: Python (installed if missing), virtual environment,
REM dependencies, templates, database, and the web interface packages.
setlocal EnableDelayedExpansion
cd /d "%~dp0"

REM Python is installed here, for the current user, when it is not found.
set "PY_VERSION=3.11.9"
set "PY_HOME=%LOCALAPPDATA%\Programs\Python\Python311"
set "PY="

echo === Python ===
call :find_python
if not defined PY (
  echo Python 3.11 or newer was not found. Installing Python %PY_VERSION% to:
  echo   %PY_HOME%
  call :install_python || goto :err
  call :find_python
)
if not defined PY (
  echo Python was installed but could not be started from %PY_HOME%.
  goto :err
)
echo Using %PY%
"%PY%" --version

echo.
echo === Backend ===
cd backend

REM Reuse the virtual environment only if it actually runs; one left half-made
REM by an earlier failed run, or copied from another PC, is rebuilt.
if exist .venv (
  .venv\Scripts\python.exe -c "import sys" >nul 2>&1
  if errorlevel 1 (
    echo The existing virtual environment is broken. Rebuilding it...
    rmdir /s /q .venv
  )
)
if not exist .venv (
  echo Creating virtual environment...
  "%PY%" -m venv .venv || goto :err
)
.venv\Scripts\python.exe -m pip install --upgrade pip -q
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :err
echo Building form templates...
.venv\Scripts\python.exe build_templates.py || goto :err
echo Preparing database...
.venv\Scripts\python.exe -m app.seed || goto :err
cd ..

echo.
echo === Frontend ===
where npm >nul 2>&1
if errorlevel 1 (
  echo Node.js was not found. Install the LTS version from https://nodejs.org
  echo then run setup.bat again.
  goto :err
)
cd frontend
call npm install || goto :err
cd ..

echo.
echo Setup complete. Run start.bat to launch the application.
pause
exit /b 0

:err
echo.
echo Setup FAILED. See the messages above.
pause
exit /b 1


REM ------------------------------------------------------------------------
REM Sets PY to the first working Python 3.11+ found. The Microsoft Store stub
REM in WindowsApps is skipped: it is not a real Python and opens the Store.
:find_python
set "PY="
call :try_python "%PY_HOME%\python.exe"
if defined PY exit /b 0
for /f "delims=" %%I in ('py -3 -c "import sys;print(sys.executable)" 2^>nul') do call :try_python "%%I"
if defined PY exit /b 0
for /f "delims=" %%I in ('where python 2^>nul') do (
  if not defined PY (
    echo %%I | findstr /i "WindowsApps" >nul || call :try_python "%%I"
  )
)
exit /b 0

:try_python
if not exist "%~1" exit /b 0
"%~1" -c "import sys;sys.exit(0 if sys.version_info>=(3,11) else 1)" >nul 2>&1
if not errorlevel 1 set "PY=%~1"
exit /b 0

REM ------------------------------------------------------------------------
REM Downloads the official installer from python.org and installs it silently
REM for the current user (no administrator rights needed), adding it to PATH.
:install_python
set "PY_ARCH=amd64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "PY_ARCH=arm64"
set "PY_INSTALLER=%TEMP%\python-%PY_VERSION%-%PY_ARCH%.exe"
set "PY_URL=https://www.python.org/ftp/python/%PY_VERSION%/python-%PY_VERSION%-%PY_ARCH%.exe"

echo Downloading %PY_URL% ...
curl.exe -L --fail -o "%PY_INSTALLER%" "%PY_URL%" 2>nul
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing -Uri '%PY_URL%' -OutFile '%PY_INSTALLER%'"
)
if not exist "%PY_INSTALLER%" (
  echo Could not download the Python installer. Check the internet connection,
  echo or install Python %PY_VERSION% manually from https://www.python.org
  exit /b 1
)

echo Installing Python %PY_VERSION% (this takes a minute or two)...
"%PY_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 InstallLauncherAllUsers=0 Include_test=0 Include_pip=1 TargetDir="%PY_HOME%"
if errorlevel 1 (
  echo The Python installer reported an error ^(code !errorlevel!^).
  del "%PY_INSTALLER%" >nul 2>&1
  exit /b 1
)
del "%PY_INSTALLER%" >nul 2>&1
echo Python installed.
exit /b 0

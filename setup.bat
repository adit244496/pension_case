@echo off
REM One-time setup: Python (installed if missing), virtual environment,
REM dependencies, templates, database, and the web interface packages.
setlocal EnableDelayedExpansion
cd /d "%~dp0"

REM Python is installed here, for the current user, when it is not found.
set "PY_VERSION=3.11.9"
set "PY_HOME=%LOCALAPPDATA%\Programs\Python\Python311"
set "PY="

REM Node is unpacked here, for the current user, when missing or too old.
set "NODE_VERSION=22.23.5"
set "NODE_MIN=22.13"
set "NODE_HOME=%LOCALAPPDATA%\Programs\nodejs22"

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
echo === Node.js ===
REM The web interface needs Node %NODE_MIN% or newer (pdfjs-dist and Vite).
REM A private copy in NODE_HOME is preferred; start.bat puts it on PATH too.
if exist "%NODE_HOME%\node.exe" set "PATH=%NODE_HOME%;%PATH%"
set "NODE_FRESH="
call :check_node
if errorlevel 1 (
  echo Node.js %NODE_MIN% or newer was not found. Installing Node %NODE_VERSION% to:
  echo   %NODE_HOME%
  call :install_node || goto :err
  set "PATH=%NODE_HOME%;!PATH!"
  set "NODE_FRESH=1"
  call :check_node
  if errorlevel 1 (
    echo Node was installed but could not be started from %NODE_HOME%.
    goto :err
  )
)
node -p "'Using ' + process.execPath + ' (' + process.version + ')'"

echo.
echo === Frontend ===
cd frontend
REM Packages installed by an older Node/npm can be incomplete; start clean.
if defined NODE_FRESH if exist node_modules (
  echo Removing packages installed by the old Node version...
  rmdir /s /q node_modules
)
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

REM ------------------------------------------------------------------------
REM Exit code 0 when "node" on PATH is version NODE_MIN or newer.
:check_node
where node >nul 2>&1 || exit /b 1
node -e "var v=process.versions.node.split('.').map(Number),m='%NODE_MIN%'.split('.').map(Number);process.exit(v[0]>m[0]||(v[0]===m[0]&&v[1]>=m[1])?0:1)" >nul 2>&1
exit /b %errorlevel%

REM ------------------------------------------------------------------------
REM Downloads the official Node.js zip and unpacks it into NODE_HOME. No
REM installer and no administrator rights; an existing system Node is untouched.
:install_node
set "NODE_ARCH=x64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "NODE_ARCH=arm64"
set "NODE_PKG=node-v%NODE_VERSION%-win-%NODE_ARCH%"
set "NODE_ZIP=%TEMP%\%NODE_PKG%.zip"
set "NODE_TMP=%TEMP%\%NODE_PKG%-unpack"
set "NODE_URL=https://nodejs.org/dist/v%NODE_VERSION%/%NODE_PKG%.zip"

echo Downloading %NODE_URL% ...
curl.exe -L --fail -o "%NODE_ZIP%" "%NODE_URL%" 2>nul
if errorlevel 1 (
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing -Uri '%NODE_URL%' -OutFile '%NODE_ZIP%'"
)
if not exist "%NODE_ZIP%" (
  echo Could not download Node.js. Check the internet connection, or install
  echo Node.js %NODE_VERSION% LTS manually from https://nodejs.org
  exit /b 1
)

echo Unpacking Node.js...
if exist "%NODE_TMP%" rmdir /s /q "%NODE_TMP%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Expand-Archive -LiteralPath '%NODE_ZIP%' -DestinationPath '%NODE_TMP%' -Force"
if not exist "%NODE_TMP%\%NODE_PKG%\node.exe" (
  echo Could not unpack %NODE_ZIP%.
  exit /b 1
)
if exist "%NODE_HOME%" rmdir /s /q "%NODE_HOME%"
if not exist "%LOCALAPPDATA%\Programs" mkdir "%LOCALAPPDATA%\Programs"
move "%NODE_TMP%\%NODE_PKG%" "%NODE_HOME%" >nul || exit /b 1
rmdir /s /q "%NODE_TMP%" >nul 2>&1
del "%NODE_ZIP%" >nul 2>&1
echo Node.js installed.
exit /b 0

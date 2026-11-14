@echo off
REM Builds the portable Windows copy: one folder with an .exe inside, for a
REM machine that has Word but no Python and no Node.
REM
REM Run this here, on the machine that has the development tools. Then copy
REM dist\PensionCase to the other machine and double-click PensionCase.exe.
setlocal
cd /d "%~dp0"

if not exist backend\.venv (
  echo Run setup.bat first.
  exit /b 1
)

echo === Web interface ===
cd frontend
call npm run build || goto :err
cd ..

echo.
echo === Form templates ===
call backend\.venv\Scripts\python.exe backend\build_templates.py || goto :err

echo.
echo === Packaging ===
backend\.venv\Scripts\python.exe -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo Installing PyInstaller into the virtual environment ...
  call backend\.venv\Scripts\python.exe -m pip install --quiet pyinstaller || goto :err
)
call backend\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean pension.spec || goto :err

copy /y deploy\portable-readme.txt dist\PensionCase\README.txt >nul

echo.
echo Built dist\PensionCase
echo Copy that whole folder to the other machine and run PensionCase.exe there.
goto :eof

:err
echo.
echo Build FAILED. See the messages above.
exit /b 1

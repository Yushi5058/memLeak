@echo off
REM Build a single-file Windows executable for memLeak.
REM
REM Run from the repository root, either by double-clicking this file or with
REM     tools\build_windows.bat
REM
REM Produces dist-windows\dist\memLeak-1.1.exe, which needs no Python install
REM on the machine that runs it.

setlocal
cd /d "%~dp0.."

echo.
echo === memLeak Windows build ===
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [X] Python was not found on PATH.
    echo     Install Python 3.10 or newer from https://python.org/downloads/
    echo     and tick "Add python.exe to PATH" during setup.
    goto :fail
)

if not exist ".venv-build\Scripts\python.exe" (
    echo [1/3] Creating the build environment .venv-build ...
    python -m venv .venv-build
    if errorlevel 1 goto :fail
) else (
    echo [1/3] Reusing the existing .venv-build environment.
)

call ".venv-build\Scripts\activate.bat"
if errorlevel 1 goto :fail

echo [2/3] Installing the pinned build dependencies ...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet "pyinstaller==6.22.3" "pygame-ce==2.5.8"
if errorlevel 1 goto :fail

echo [3/3] Bundling the game. This takes a minute or two ...
python tools\build_executable.py --onefile --outdir dist-windows
if errorlevel 1 goto :fail

echo.
echo === Done ===
echo.
echo The finished program is:
echo     %CD%\dist-windows\dist\memLeak-1.1.exe
echo.
echo Copy that one file to a USB stick or a chat message. It runs on any
echo 64-bit Windows 10 or newer with no Python installed.
echo.
echo Note: the file is not code-signed, so SmartScreen may warn that the
echo publisher is unknown. Choose "More info" then "Run anyway".
echo.
pause
exit /b 0

:fail
echo.
echo [X] The build did not finish. Fix the problem above and run it again.
echo.
pause
exit /b 1

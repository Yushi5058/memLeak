@echo off
REM Build a single-file Windows executable for memLeak.
REM
REM Run from the repository root, either by double-clicking this file or with
REM     tools\build_windows.bat
REM
REM Produces dist-windows\dist\memLeak-1.1.exe, which needs no Python install
REM on the machine that runs it.
REM
REM If the build fails partway through with "file name too long" or a path
REM related error, clone the repository somewhere short like C:\src\memLeak.
REM The onefile bundle pulls in over a hundred shared libraries under
REM _internal, and the default MAX_PATH limit of 260 characters is easy to
REM exceed from inside Documents.

setlocal
cd /d "%~dp0.."

echo.
echo === memLeak Windows build ===
echo.

rem "where python" also succeeds for the Microsoft Store alias on Windows 10 and
rem 11, which opens the Store and exits instead of running anything. Probe for a
rem real interpreter of a usable version rather than just its presence.
python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [X] No usable Python 3.10 or newer was found on PATH.
    echo     Install it from https://www.python.org/downloads/
    echo     and tick "Add python.exe to PATH" during setup.
    echo     If the Microsoft Store opened instead, close it: that is the Store
    echo     alias pretending to be Python, not a real install.
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
rem Onefile is the default; there is no --onefile flag, only --onedir.
python tools\build_executable.py --outdir dist-windows
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

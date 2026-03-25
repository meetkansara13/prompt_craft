@echo off
REM ═══════════════════════════════════════════════════════════════
REM  PromptCraft Pro v3 — Start App
REM  Run from Anaconda Prompt, from inside D:\promptcraft_v3\
REM
REM  Requires: setup.bat to have been run first
REM ═══════════════════════════════════════════════════════════════

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║   PromptCraft Pro v3                     ║
echo   ╚══════════════════════════════════════════╝
echo.

REM ── Check we are in the right folder ──────────────────────────
IF NOT EXIST run.py (
    echo   ERROR: run.py not found.
    echo   Make sure you are inside the promptcraft_v3 folder.
    echo.
    echo   Example:
    echo     D:
    echo     cd promptcraft_v3
    echo     run.bat
    echo.
    pause
    exit /b 1
)

REM ── Check .env exists ─────────────────────────────────────────
IF NOT EXIST .env (
    echo   ERROR: .env not found.
    echo   Run setup.bat first.
    echo.
    pause
    exit /b 1
)

REM ── Activate conda environment ────────────────────────────────
echo   Activating conda environment "promptcraft"...
call conda activate promptcraft

IF ERRORLEVEL 1 (
    echo.
    echo   WARNING: Could not activate "promptcraft" environment.
    echo   Run setup.bat first if you have not done the setup yet.
    echo.
    echo   Trying to run anyway with current Python...
    echo.
)

REM ── Start the server ──────────────────────────────────────────
echo   Starting server...
echo.
echo   ┌─────────────────────────────────────┐
echo   │  Open in browser:                   │
echo   │  http://localhost:5000              │
echo   │                                     │
echo   │  Press Ctrl+C to stop               │
echo   └─────────────────────────────────────┘
echo.

python run.py

echo.
echo   Server stopped.
pause

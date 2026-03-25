@echo off
REM ═══════════════════════════════════════════════════════════════
REM  PromptCraft Pro v3 — Full Setup
REM  Run from Anaconda Prompt, from inside D:\promptcraft_v3\
REM
REM  What this does:
REM    1. Checks you are in the right folder
REM    2. Creates conda environment "promptcraft" (Python 3.11)
REM    3. Activates it
REM    4. Copies .env.example → .env (if not already there)
REM    5. Opens .env in Notepad so you can add your API key
REM    6. Verifies all packages installed correctly
REM ═══════════════════════════════════════════════════════════════

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║   PromptCraft Pro v3 — Setup             ║
echo   ╚══════════════════════════════════════════╝
echo.

REM ── Check environment.yml exists (means we're in the right folder)
IF NOT EXIST environment.yml (
    echo   ERROR: environment.yml not found.
    echo   Make sure you are inside the promptcraft_v3 folder.
    echo.
    echo   Example:
    echo     D:
    echo     cd promptcraft_v3
    echo     setup.bat
    echo.
    pause
    exit /b 1
)

echo   Folder: OK
echo   Location: %CD%
echo.

REM ── STEP 1: Create conda environment ──────────────────────────
echo   [Step 1/4]  Creating conda environment "promptcraft"...
echo   This may take a few minutes on first run.
echo.

call conda env create -f environment.yml

IF ERRORLEVEL 1 (
    echo.
    echo   The environment may already exist.
    echo   Trying to update it instead...
    echo.
    call conda env update -f environment.yml --prune
    IF ERRORLEVEL 1 (
        echo.
        echo   ERROR: Could not create or update the conda environment.
        echo   Try manually:
        echo     conda env remove -n promptcraft
        echo     conda env create -f environment.yml
        echo.
        pause
        exit /b 1
    )
)

echo.
echo   Environment created.

REM ── STEP 2: Activate environment ──────────────────────────────
echo.
echo   [Step 2/4]  Activating "promptcraft" environment...
echo.

call conda activate promptcraft

IF ERRORLEVEL 1 (
    echo.
    echo   WARNING: Could not auto-activate in this script.
    echo   After setup finishes, run:
    echo     conda activate promptcraft
    echo.
)

REM ── STEP 3: Set up .env file ───────────────────────────────────
echo   [Step 3/4]  Setting up .env config file...
echo.

IF NOT EXIST .env (
    copy .env.example .env > nul
    echo   Created .env from .env.example
) ELSE (
    echo   .env already exists — keeping your existing config
)

REM Open .env in Notepad so user can add their API key
echo.
echo   Opening .env in Notepad...
echo   ╔══════════════════════════════════════════════════════╗
echo   ║  IMPORTANT: Replace the placeholder values:          ║
echo   ║                                                       ║
echo   ║  ANTHROPIC_API_KEY=sk-ant-api03-your-key-here        ║
echo   ║                ↑ paste your real key here             ║
echo   ║                                                       ║
echo   ║  FLASK_SECRET_KEY=change-this-to-a-random-string     ║
echo   ║                ↑ type anything random here            ║
echo   ║                                                       ║
echo   ║  Get a free key: https://console.anthropic.com       ║
echo   ╚══════════════════════════════════════════════════════╝
echo.
echo   Press any key to open Notepad...
pause > nul
notepad .env

REM ── STEP 4: Verify packages ────────────────────────────────────
echo.
echo   [Step 4/4]  Verifying installed packages...
echo.

python -c "import flask; print('  flask ............. OK')"
python -c "import anthropic; print('  anthropic ......... OK')"
python -c "import pydantic; print('  pydantic .......... OK')"
python -c "import dotenv; print('  python-dotenv ..... OK')"
python -c "import pytest; print('  pytest ............ OK')"

IF ERRORLEVEL 1 (
    echo.
    echo   Some packages failed. Try:
    echo     pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM ── Done ──────────────────────────────────────────────────────
echo.
echo   ╔══════════════════════════════════════════════════════╗
echo   ║   Setup complete!                                     ║
echo   ║                                                       ║
echo   ║   To start the app:                                   ║
echo   ║     conda activate promptcraft                        ║
echo   ║     python run.py                                     ║
echo   ║                                                       ║
echo   ║   Or just double-click:  run.bat                      ║
echo   ║                                                       ║
echo   ║   Then open: http://localhost:5000                    ║
echo   ╚══════════════════════════════════════════════════════╝
echo.
pause

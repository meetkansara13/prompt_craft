@echo off
REM ═══════════════════════════════════════════════════════════════
REM  PromptCraft Pro v3 — Run Tests
REM  No API key needed — Anthropic is mocked in all tests
REM ═══════════════════════════════════════════════════════════════

echo.
echo   ╔══════════════════════════════════════════╗
echo   ║   PromptCraft Pro v3 — Tests             ║
echo   ╚══════════════════════════════════════════╝
echo.

call conda activate promptcraft 2>nul

echo   Running all tests...
echo   (No API key needed — Anthropic calls are mocked)
echo.

pytest tests\ -v

echo.
pause

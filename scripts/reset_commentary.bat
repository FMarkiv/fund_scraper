@echo off
REM ============================================
REM  Reset Commentary Template
REM  Clears commentary.md for a fresh start
REM ============================================

cd /d C:\fund_scraper

echo.
echo This will reset commentary.md to a blank template.
echo.
set /p CONFIRM="Continue? (y/n): "

if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

REM Backup existing commentary
if exist commentary.md (
    copy commentary.md commentary_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.md >nul
    echo Backup saved: commentary_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.md
)

REM Write fresh template
(
echo ## Fixed Income
echo.
echo.
echo.
echo ## Private Credit
echo.
echo.
echo.
echo ## Domestic Large Cap
echo.
echo.
echo.
echo ## Domestic Mid/Small Cap
echo.
echo.
echo.
echo ## Domestic Micro Cap
echo.
echo.
echo.
echo ## International Equities
echo.
echo.
echo.
echo ## Infra + REITs
echo.
echo.
echo.
echo ## Other
echo.
echo.
echo.
echo ## GICS Sectors
echo.
echo.
echo.
echo ## Crypto
echo.
echo.
echo.
echo ## Thought of the Month
echo.
echo.
echo.
echo ## Thanks
echo.
echo Thanks for reading. See you next month.
echo.
) > commentary.md

echo.
echo ============================================
echo  commentary.md has been reset!
echo ============================================
echo.
echo Workflow:
echo   1. Run: scripts\generate.bat YYYY-MM-DD YYYY-MM --preview
echo   2. Review data in browser
echo   3. Edit commentary.md with your insights
echo   4. Re-run: scripts\generate.bat YYYY-MM-DD YYYY-MM
echo.
pause

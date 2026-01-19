@echo off
REM ============================================
REM  Newsletter Generator - One Command
REM  Usage: generate.bat 2025-01-31 2025-01
REM         generate.bat [end-date] [month]
REM ============================================

cd /d C:\fund_scraper

REM Check arguments
if "%~1"=="" (
    echo.
    echo Usage: generate.bat [end-date] [newsletter-month]
    echo.
    echo Example: generate.bat 2025-01-31 2025-01
    echo          generate.bat 2025-03-31 2025-03
    echo.
    echo   end-date: Last day of month for benchmark prices ^(YYYY-MM-DD^)
    echo   month:    Newsletter month ^(YYYY-MM^)
    echo.
    pause
    exit /b 1
)

if "%~2"=="" (
    echo Error: Missing newsletter month parameter
    echo Usage: generate.bat 2025-01-31 2025-01
    pause
    exit /b 1
)

set END_DATE=%~1
set MONTH=%~2

echo ============================================
echo  NEWSLETTER GENERATOR
echo  End Date: %END_DATE%
echo  Month:    %MONTH%
echo ============================================

REM Step 1: Fetch benchmark data
echo.
echo [1/4] Fetching benchmark data for %END_DATE%...
python fetch_benchmarks.py --date %END_DATE%
if errorlevel 1 (
    echo ERROR: Benchmark fetch failed!
    pause
    exit /b 1
)

REM Step 2: Show coverage status
echo.
echo [2/4] Checking data coverage...
python check_coverage.py

REM Step 3: Generate preview
echo.
echo [3/4] Generating newsletter preview...
python generate_newsletter.py --month %MONTH% --preview
if errorlevel 1 (
    echo ERROR: Newsletter generation failed!
    pause
    exit /b 1
)

REM Step 4: Prompt for final generation
echo.
echo ============================================
echo  Preview opened in browser.
echo  Review the newsletter before continuing.
echo ============================================
echo.
set /p CONFIRM="Generate final newsletter? (y/n): "

if /i "%CONFIRM%"=="y" (
    echo.
    echo [4/4] Generating final newsletter...
    python generate_newsletter.py --month %MONTH%
    echo.
    echo ============================================
    echo  SUCCESS! Newsletter saved to:
    echo  newsletter_%MONTH:.=_%.html
    echo ============================================
) else (
    echo.
    echo Cancelled. Edit commentary.md and run again.
)

echo.
pause

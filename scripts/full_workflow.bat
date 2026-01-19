@echo off
REM ============================================
REM  Full Newsletter Workflow
REM  Runs all steps in sequence
REM  Usage: full_workflow.bat 2025-01-31 2025-01
REM ============================================

cd /d C:\fund_scraper

if "%~1"=="" (
    echo.
    echo Usage: full_workflow.bat [end-date] [newsletter-month]
    echo.
    echo Example: full_workflow.bat 2025-01-31 2025-01
    echo.
    pause
    exit /b 1
)

if "%~2"=="" (
    echo Error: Missing newsletter month
    pause
    exit /b 1
)

set END_DATE=%~1
set MONTH=%~2

echo.
echo ============================================
echo  FULL NEWSLETTER WORKFLOW
echo  End Date: %END_DATE%
echo  Month:    %MONTH%
echo ============================================
echo.
echo This will run:
echo   1. Process S&P PDFs (if available)
echo   2. Run fund scraper (~2-3 hours)
echo   3. Fetch benchmarks
echo   4. Generate newsletter
echo.
set /p START="Start full workflow? (y/n): "
if /i not "%START%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

REM Step 1: Process S&P PDFs if available
echo.
echo ============================================
echo  STEP 1: Processing S&P PDFs
echo ============================================
if exist "index\pdfs\*.pdf" (
    call scripts\process_sp_pdfs.bat
) else (
    echo No PDFs found in index\pdfs\ - skipping
    echo ^(Download manually when available^)
)

REM Step 2: Run scraper
echo.
echo ============================================
echo  STEP 2: Running Fund Scraper
echo  This will take 2-3 hours...
echo ============================================
echo.
set /p SCRAPE="Run scraper now? (y/n/skip): "
if /i "%SCRAPE%"=="y" (
    python fund_scraper.py
    python check_coverage.py
) else if /i "%SCRAPE%"=="skip" (
    echo Skipping scraper - using existing data
) else (
    echo Cancelled.
    pause
    exit /b 0
)

REM Step 3: Generate newsletter
echo.
echo ============================================
echo  STEP 3: Generating Newsletter
echo ============================================
call scripts\generate.bat %END_DATE% %MONTH%

echo.
echo ============================================
echo  WORKFLOW COMPLETE!
echo ============================================
echo.
echo Next steps:
echo   1. Upload newsletter_%MONTH:.=_%.html to ausyield.com.au
echo   2. Copy content to Substack
echo   3. Share on LinkedIn
echo.
echo Run: scripts\linkedin_post.bat %MONTH%
echo.
pause

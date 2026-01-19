@echo off
REM ============================================
REM  Fund Scraper - Overnight Automation
REM  Schedule this with Windows Task Scheduler
REM  Recommended: 16th of each month at 11:00 PM
REM ============================================

echo ============================================
echo  FUND SCRAPER - Started at %date% %time%
echo ============================================

cd /d C:\fund_scraper

REM Run the main scraper
echo.
echo [1/3] Running fund scraper...
python fund_scraper.py

REM Check coverage and save report
echo.
echo [2/3] Checking coverage...
python check_coverage.py > coverage_report_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt 2>&1

REM Show summary
echo.
echo [3/3] Scraping complete!
echo.
echo Coverage report saved to: coverage_report_%date:~-4,4%%date:~-10,2%%date:~-7,2%.txt
echo.
echo ============================================
echo  COMPLETED at %time%
echo ============================================

REM Keep window open if run manually
pause

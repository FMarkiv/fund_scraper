@echo off
REM ============================================
REM  LinkedIn Post Generator
REM  Creates a draft post and copies to clipboard
REM  Usage: linkedin_post.bat 2025-01
REM ============================================

cd /d C:\fund_scraper

if "%~1"=="" (
    echo.
    echo Usage: linkedin_post.bat [newsletter-month]
    echo Example: linkedin_post.bat 2025-01
    echo.
    pause
    exit /b 1
)

set MONTH=%~1

REM Parse month name
for /f "tokens=1,2 delims=-" %%a in ("%MONTH%") do (
    set YEAR=%%a
    set MON=%%b
)

REM Convert month number to name
if "%MON%"=="01" set MONTH_NAME=January
if "%MON%"=="02" set MONTH_NAME=February
if "%MON%"=="03" set MONTH_NAME=March
if "%MON%"=="04" set MONTH_NAME=April
if "%MON%"=="05" set MONTH_NAME=May
if "%MON%"=="06" set MONTH_NAME=June
if "%MON%"=="07" set MONTH_NAME=July
if "%MON%"=="08" set MONTH_NAME=August
if "%MON%"=="09" set MONTH_NAME=September
if "%MON%"=="10" set MONTH_NAME=October
if "%MON%"=="11" set MONTH_NAME=November
if "%MON%"=="12" set MONTH_NAME=December

REM Create the post
set POST_FILE=linkedin_post_%MONTH:.=_%.txt

echo Creating LinkedIn post draft...

(
echo ============================================
echo  LINKEDIN POST - %MONTH_NAME% %YEAR%
echo  Copy everything below the line
echo ============================================
echo.
echo -------------------------------------------
echo.
echo 📊 %MONTH_NAME% %YEAR% Market Update
echo.
echo Key highlights from this month's newsletter:
echo.
echo • [Best performing asset class: XX%% 1-month return]
echo • [Worst performing: XX%%]
echo • [Notable fund movement or trend]
echo • [Key insight from Thought of the Month]
echo.
echo Full newsletter with performance tables across:
echo ✓ Fixed Income
echo ✓ Australian Equities ^(Large/Mid/Small/Micro Cap^)
echo ✓ International Equities
echo ✓ GICS Sectors
echo ✓ Crypto ^& Commodities
echo.
echo 🔗 Read the full newsletter: https://ausyield.com.au/newsletter.html
echo.
echo ---
echo.
echo #investing #australianstocks #asxstocks #markets #financialmarkets #wealthmanagement #fundperformance
echo.
echo -------------------------------------------
) > %POST_FILE%

echo.
echo ============================================
echo  LinkedIn post draft created!
echo  File: %POST_FILE%
echo ============================================
echo.
echo Edit the post to fill in:
echo   - Best/worst performing asset classes
echo   - Notable fund movements
echo   - Key insight from your commentary
echo.

REM Open the file for editing
notepad %POST_FILE%

echo.
pause

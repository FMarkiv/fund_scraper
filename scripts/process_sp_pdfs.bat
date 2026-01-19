@echo off
REM ============================================
REM  S&P PDF Processor
REM  Run after manually downloading PDFs to index/pdfs/
REM ============================================

cd /d C:\fund_scraper

echo ============================================
echo  S&P PDF PROCESSOR
echo ============================================

REM Check if PDFs exist
if not exist "index\pdfs\*.pdf" (
    echo.
    echo ERROR: No PDF files found in index\pdfs\
    echo.
    echo Please download S&P factsheet PDFs first:
    echo   1. Go to S&P Global website
    echo   2. Download each sector factsheet
    echo   3. Save to: C:\fund_scraper\index\pdfs\
    echo.
    pause
    exit /b 1
)

REM Count PDFs
for /f %%a in ('dir /b "index\pdfs\*.pdf" 2^>nul ^| find /c /v ""') do set PDF_COUNT=%%a
echo.
echo Found %PDF_COUNT% PDF files in index\pdfs\

REM Step 1: Extract data from PDFs
echo.
echo [1/2] Extracting performance data from PDFs...
cd index
python pdfscraper.py
if errorlevel 1 (
    echo ERROR: PDF extraction failed!
    cd ..
    pause
    exit /b 1
)
cd ..
echo     Output: index/performance_data.csv

REM Step 2: Merge into manual_data.xlsx
echo.
echo [2/2] Merging S&P data into manual_data.xlsx...
python merge_sp_data.py
if errorlevel 1 (
    echo ERROR: Merge failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  SUCCESS! S&P data processed and merged.
echo  GICS sectors updated in manual_data.xlsx
echo ============================================
echo.
pause

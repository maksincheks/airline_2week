@echo off
setlocal

echo Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Error: Dependencies failed to install. Check requirements.txt.
    pause
    exit /b 1
)

if not exist "data" mkdir data

echo Running the scraper...
scrapy crawl airline --logfile=scrapy.log
if %ERRORLEVEL% neq 0 (
    echo Error: Scraping failed. Check scrapy.log for details.
    pause
    exit /b 1
)

echo Scraping completed successfully. Results are in the "data" folder.
pause
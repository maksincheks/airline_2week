@echo off
setlocal

:: Проверка наличия Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python not download or not add in PATH.
    pause
    exit /b 1
)


:: Проверяем, установлен ли Scrapy
set PYTHON="C:\Users\maksi\AppData\Local\Programs\Python\Python311\python.exe"

%PYTHON% -c "import scrapy" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Scrapy не установлен. Устанавливаем...
    %PYTHON% -m pip install scrapy
)

:: Создание папки outputs, если её нет
if not exist "outputs" mkdir outputs

:: Запуск паука
echo.
echo ========================================
echo Star parser airline.su
echo ========================================
echo.

%PYTHON% -m scrapy crawl airline --loglevel=INFO

if %ERRORLEVEL% equ 0 (
    echo Parsing succesfull. Results save in outputs.
) else (
    echo An error has occurred	.
)

pause
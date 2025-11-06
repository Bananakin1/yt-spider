@echo off
REM View the latest bot log file

cd /d "%~dp0"

if not exist "logs" (
    echo No logs directory found.
    echo The bot hasn't run yet.
    pause
    exit /b 1
)

REM Find the most recent log file
for /f "delims=" %%i in ('dir /b /o-d logs\bot_*.log 2^>nul') do (
    set LATEST_LOG=%%i
    goto :found
)

:not_found
echo No log files found.
echo The bot hasn't run yet.
pause
exit /b 1

:found
echo.
echo ============================================================
echo LATEST LOG FILE: %LATEST_LOG%
echo ============================================================
echo.
type "logs\%LATEST_LOG%"
echo.
echo.
echo ============================================================
echo END OF LOG
echo ============================================================
echo.
pause

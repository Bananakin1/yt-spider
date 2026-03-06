@echo off
REM YouTube Discord Bot Runner
REM This batch file activates the virtual environment and runs the bot

REM Change to script directory
cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Generate timestamp for log file name (format: YYYY-MM-DD_HH-MM-SS)
REM Using PowerShell instead of deprecated WMIC (removed in Windows 11 24H2+)
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'"') do set TIMESTAMP=%%i
set LOGFILE=logs\bot_%TIMESTAMP%.log

REM Run the bot and save output to log file
echo ========================================== >> "%LOGFILE%"
echo Bot started at %date% %time% >> "%LOGFILE%"
echo ========================================== >> "%LOGFILE%"
echo. >> "%LOGFILE%"

call venv\Scripts\activate.bat
python youtube_discord_bot.py >> "%LOGFILE%" 2>&1
set ERRORLEVEL_BACKUP=%ERRORLEVEL%

echo. >> "%LOGFILE%"
echo ========================================== >> "%LOGFILE%"
echo Bot finished at %date% %time% >> "%LOGFILE%"
echo Exit code: %ERRORLEVEL_BACKUP% >> "%LOGFILE%"
echo ========================================== >> "%LOGFILE%"

deactivate
exit /b %ERRORLEVEL_BACKUP%

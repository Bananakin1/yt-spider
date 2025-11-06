@echo off
REM YouTube Discord Bot Runner
REM This batch file activates the virtual environment and runs the bot

REM Change to script directory
cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Generate timestamp for log file name (format: YYYY-MM-DD_HH-MM-SS)
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set LOGFILE=logs\bot_%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%_%datetime:~8,2%-%datetime:~10,2%-%datetime:~12,2%.log

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

@echo off
REM Relegated to WSL copy at ~/dev/yt-bot. Windows venv is retired.
REM Logs written to ~/dev/yt-bot/logs/bot_<timestamp>.log
wsl -d Ubuntu bash -lc "cd ~/dev/yt-bot && mkdir -p logs && source venv/bin/activate && TS=$(date +%%Y-%%m-%%d_%%H-%%M-%%S) && { echo ==========================================; echo Bot started at $(date); echo ==========================================; echo; python youtube_discord_bot.py; RC=$?; echo; echo ==========================================; echo Bot finished at $(date); echo Exit code: $RC; echo ==========================================; exit $RC; } >> logs/bot_$TS.log 2>&1"
exit /b %ERRORLEVEL%

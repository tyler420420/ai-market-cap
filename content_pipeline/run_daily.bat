@echo off
:: ============================================================
:: BLOGGER PIPELINE - 8 AM PUBLISH
:: Article WRITING happens at 7 AM via the daily_traffic_articles
:: agent cron (trending scan -> write -> quality gate).
:: This task publishes whatever passed the gate, notifies Bing via
:: IndexNow (Google via sitemap.xml + robots.txt), then VERIFIES the
:: served site. A failed verification is logged loudly, not swallowed.
:: ============================================================

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: 1. Safety net: score anything sitting in the queue before it publishes
python daily_content_pipeline.py gate

:: 2. Publish approved articles + submit to search engines
python blog_to_railway.py

:: 3. Verify what Railway ACTUALLY served. Railway needs ~60s to redeploy,
::    so wait before checking, then gate the exit code on the result.
echo [%date% %time%] Waiting 75s for Railway redeploy... >> ..\traffic_publish.log
:: `timeout` needs an interactive console and fails under Task Scheduler.
:: `ping` to loopback is the reliable non-interactive sleep.
ping -n 76 127.0.0.1 > nul

python verify_blogger_lane.py > ..\verify_blogger_lane.out 2>&1
set VERIFY_RESULT=%ERRORLEVEL%

if %VERIFY_RESULT%==0 (
    echo [%date% %time%] VERIFY PASSED — served site matches index.json >> ..\traffic_publish.log
) else (
    echo [%date% %time%] VERIFY FAILED ^(exit %VERIFY_RESULT%^) — served site is wrong. See verify_blogger_lane.out >> ..\traffic_publish.log
    type ..\verify_blogger_lane.out >> ..\traffic_publish.log
)

echo [%date% %time%] Blogger pipeline published >> ..\traffic_publish.log
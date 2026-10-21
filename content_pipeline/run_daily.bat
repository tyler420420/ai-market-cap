@echo off
:: ============================================================
:: BLOGGER PIPELINE - 8 AM PUBLISH
:: Article WRITING happens at 7 AM via the daily_traffic_articles
:: agent cron (trending scan -> write -> quality gate).
:: This task publishes whatever passed the gate, then notifies
:: Bing via IndexNow. Google is covered by sitemap.xml + robots.txt.
:: ============================================================

cd /d "%~dp0"

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

:: 1. Safety net: score anything sitting in the queue before it publishes
python daily_content_pipeline.py gate

:: 2. Publish approved articles + submit to search engines
python blog_to_railway.py

echo [%date% %time%] Blogger pipeline published >> ..\traffic_publish.log
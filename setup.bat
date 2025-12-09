@echo off
REM RTINA Traffic Navigation Project Automated Setup (Windows)
REM Author: AI Assistant
REM Date: 2025-11-07

SET ROOT=C:\traffic-project

REM Create folders
mkdir "%ROOT%\backend"
mkdir "%ROOT%\backend\data"
mkdir "%ROOT%\backend\videos"
mkdir "%ROOT%\frontend"
mkdir "%ROOT%\frontend\assets"
mkdir "%ROOT%\data"
mkdir "%ROOT%\docs"
mkdir "%ROOT%\logs"

REM Copy Python core files if available in current folder
REM Adjust source paths if your files are elsewhere:
copy "%ROOT%\config.py" "%ROOT%\backend\config.py"
copy "%ROOT%\database.py" "%ROOT%\backend\database.py"
copy "%ROOT%\video_processor.py" "%ROOT%\backend\video_processor.py"
copy "%ROOT%\pathfinding.py" "%ROOT%\backend\pathfinding.py"
copy "%ROOT%\app.py" "%ROOT%\backend\app.py"
copy "%ROOT%\requirements.txt" "%ROOT%\backend\requirements.txt"
copy "%ROOT%\environment.yml" "%ROOT%\environment.yml"
copy "%ROOT%\nagpur_roads.json" "%ROOT%\data\nagpur_roads.json"

REM Copy frontend files
copy "%ROOT%\index.html" "%ROOT%\frontend\index.html"
copy "%ROOT%\style.css" "%ROOT%\frontend\style.css"
copy "%ROOT%\script.js" "%ROOT%\frontend\script.js"

REM Reminder for videos
echo Please copy your 5 intersection videos (MP4, 30sec) to:
echo   %ROOT%\backend\videos\
echo Videos should be named: intersection_1.mp4 to intersection_5.mp4

REM Setup instructions
echo ---------------------------------------------------------
echo To continue:
echo 1. Open Anaconda Prompt (as Administrator)
echo 2. Run:
echo      cd %ROOT%
echo      conda env create -f environment.yml
echo      conda activate rtina-env
echo      python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
echo 3. Open your browser to http://localhost:8000
echo ---------------------------------------------------------
pause

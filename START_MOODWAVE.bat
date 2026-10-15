@echo off
title MoodWave - Auto Start
cd /d "%~dp0"
echo Starting MoodWave Servers...
python run_all.py
pause


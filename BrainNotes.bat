@echo off
title BrainNotes
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (python server.py) else (py server.py)
if errorlevel 1 pause

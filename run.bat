@echo off
REM ============================================================
REM  AFL Ladder Bet - launcher
REM  Double-click this file to start the app in your browser.
REM  Always uses Python 3.13 (the interpreter that has Streamlit
REM  + anthropic installed) to avoid "ModuleNotFoundError".
REM ============================================================
cd /d "%~dp0"
echo Starting AFL Ladder Bet...
echo The app will open at http://localhost:8501
echo Close this window to stop the app.
echo.
py -V:3.13 -m streamlit run app.py
pause

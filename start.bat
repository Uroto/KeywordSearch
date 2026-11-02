@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul && (py -m streamlit run app.py) || (python -m streamlit run app.py)
pause

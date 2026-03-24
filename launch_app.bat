@echo off
cd /d "%~dp0"

:: This uses the venv Python to run Streamlit directly
.\venv\Scripts\python.exe -m streamlit run app.py

pause
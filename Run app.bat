@echo off
TITLE Streamlit App Launcher

:: This ensures the script runs in your project folder
cd /d "%~dp0"

:: Check if the virtual environment is already set up
IF NOT EXIST "venv\Scripts\python.exe" (
    echo ========================================================
    echo First run detected! Setting up the virtual environment...
    echo This might take a few minutes depending on your internet.
    echo ========================================================
    
    :: Create the virtual environment
    python -m venv venv
    
    :: Upgrade pip just to be safe
    .\venv\Scripts\python.exe -m pip install --upgrade pip
    
    :: Install all the libraries from your requirements.txt
    echo Installing required libraries...
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
    
    echo Setup complete! Launching app...
) ELSE (
    echo Virtual environment found. Starting the app...
)

:: Run the Streamlit app using the venv's Python
.\venv\Scripts\python.exe -m streamlit run app.py

:: Keep the window open if something crashes so you can read the error
pause
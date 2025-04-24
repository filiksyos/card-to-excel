@echo off
echo Running Medical Card Age Extraction tool...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the script
python main.py

echo.
echo Process complete! Check the output directory for results.
echo.

pause 
@echo off
echo Setting up the Medical Card Age Extraction tool...

REM Create directories if they don't exist
if not exist images mkdir images
if not exist output mkdir output

REM Check if .env file exists, if not create it
if not exist .env (
    echo Creating .env file...
    echo # API Configuration > .env
    echo OPENROUTER_API_KEY=your_openrouter_api_key_here >> .env
    echo. >> .env
    echo # Directories >> .env
    echo IMAGE_DIR=images >> .env
    echo OUTPUT_DIR=output >> .env
    echo. >> .env
    echo # Excel >> .env
    echo EXCEL_TEMPLATE=template.xlsx >> .env
    echo EXCEL_OUTPUT=output/age_extracted_data.xlsx >> .env
    echo. >> .env
    echo # Logging >> .env
    echo LOG_LEVEL=INFO >> .env
    echo LOG_FILE=app.log >> .env
    echo Created .env file. Please edit it to add your OpenRouter API key.
) else (
    echo .env file already exists.
)

REM Check if virtual environment exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt

echo.
echo Setup complete! You need to:
echo 1. Edit the .env file to add your OpenRouter API key
echo 2. Place your medical card images in the 'images' folder
echo 3. Run the script with: python main.py
echo.

pause 
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.0-flash-001"  # Updated to gpt-4.1-nano

# Image Processing Configuration
IMAGE_DIR = os.getenv('IMAGE_DIR', 'images')
OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png']

# Excel Configuration
EXCEL_TEMPLATE = os.getenv('EXCEL_TEMPLATE', 'template.xlsx')
EXCEL_OUTPUT = os.getenv('EXCEL_OUTPUT', 'output/medical_cards_export_new.xlsx')  # New filename to avoid permission issues

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')  # Changed from INFO to DEBUG
LOG_FILE = os.getenv('LOG_FILE', 'app.log') 
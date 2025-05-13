import os
import shutil
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
import uvicorn
from pathlib import Path

# Import existing functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from image_handler import encode_image
from api_handler import extract_text_from_image
from data_parser import parse_extraction_result, validate_data
from excel_handler import save_to_excel
from config import EXCEL_TEMPLATE, EXCEL_OUTPUT

app = FastAPI()

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Create necessary directories
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Copy template if it doesn't exist in output
template_path = BASE_DIR / EXCEL_TEMPLATE
if template_path.exists():
    shutil.copy2(template_path, OUTPUT_DIR / EXCEL_TEMPLATE)

# Mount static files and templates with correct paths
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process")
async def process_image(file: UploadFile = File(...)):
    try:
        # Save uploaded file
        file_path = UPLOAD_DIR / file.filename
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Process image using existing functionality
        base64_image = encode_image(str(file_path))
        if not base64_image:
            raise HTTPException(status_code=400, detail="Failed to encode image")
        
        extracted_text = extract_text_from_image(base64_image)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Failed to extract text from image")
        
        parsed_data = parse_extraction_result(extracted_text)
        if not parsed_data:
            raise HTTPException(status_code=400, detail="Failed to parse extracted text")
        
        # Validate data
        is_valid, messages = validate_data(parsed_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Data validation failed: {', '.join(messages)}")
        
        # Add image filename
        parsed_data['image_filename'] = file.filename
        
        # Save to Excel
        excel_path = BASE_DIR / EXCEL_OUTPUT
        if not save_to_excel([parsed_data]):
            raise HTTPException(status_code=500, detail="Failed to save Excel file")
        
        # Clean up uploaded file
        file_path.unlink()
        
        return JSONResponse({
            "extracted_text": extracted_text,
            "excel_url": "/download"
        })
        
    except Exception as e:
        # Clean up uploaded file if it exists
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_excel():
    excel_path = BASE_DIR / EXCEL_OUTPUT
    if not excel_path.exists():
        raise HTTPException(status_code=404, detail="Excel file not found")
    return FileResponse(
        excel_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="medical_data.xlsx"
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
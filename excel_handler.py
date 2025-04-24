import os
import pandas as pd
from openpyxl import load_workbook
from config import EXCEL_TEMPLATE, EXCEL_OUTPUT, OUTPUT_DIR
from logger import get_logger

logger = get_logger(__name__)

def prepare_output_directory():
    """Ensure the output directory exists."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    logger.info(f"Ensured output directory exists: {OUTPUT_DIR}")

def save_to_excel(data_list):
    """
    Save the extracted age and sex data to an Excel file.
    
    Args:
        data_list (list): List of dictionaries containing extracted age and sex data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Make sure the output directory exists
        prepare_output_directory()
        
        # Check if we have a template
        if os.path.exists(EXCEL_TEMPLATE):
            logger.info(f"Using Excel template: {EXCEL_TEMPLATE}")
            # Load the template
            workbook = load_workbook(EXCEL_TEMPLATE)
            sheet = workbook.active
            
            # Start row (adjust as needed based on template)
            start_row = 2
            
            # Map data to columns
            for i, data in enumerate(data_list):
                row = start_row + i
                # Assuming column A is for Age and column B is for Sex in the template
                sheet[f"A{row}"] = data.get("Age")
                sheet[f"B{row}"] = data.get("Sex")
                # Add the image filename for reference in column C
                if "image_filename" in data:
                    sheet[f"C{row}"] = data.get("image_filename")
            
            # Save the workbook
            workbook.save(EXCEL_OUTPUT)
            logger.info(f"Successfully saved data to {EXCEL_OUTPUT} based on template")
            
        else:
            # No template, create a new Excel file
            logger.warning(f"No template found at {EXCEL_TEMPLATE}, creating new Excel file")
            # Create a DataFrame with Age, Sex and image_filename columns
            simplified_data = []
            for item in data_list:
                simplified_data.append({
                    "Age": item.get("Age"),
                    "Sex": item.get("Sex"),
                    "Image Filename": item.get("image_filename", "")
                })
            df = pd.DataFrame(simplified_data)
            df.to_excel(EXCEL_OUTPUT, index=False)
            logger.info(f"Successfully saved data to {EXCEL_OUTPUT}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving to Excel: {str(e)}")
        return False 
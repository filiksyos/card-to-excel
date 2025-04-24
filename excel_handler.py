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
    Save the extracted patient name, age, sex, card number, telephone, address, kebele, and date data to an Excel file.
    
    Args:
        data_list (list): List of dictionaries containing extracted data
        
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
                # Column mapping (adjust as needed)
                sheet[f"A{row}"] = data.get("PatientName")
                sheet[f"B{row}"] = data.get("Age")
                sheet[f"C{row}"] = data.get("Sex")
                sheet[f"D{row}"] = data.get("CardNumber")
                sheet[f"E{row}"] = data.get("Telephone")
                sheet[f"F{row}"] = data.get("Address")
                sheet[f"G{row}"] = data.get("Kebele")
                sheet[f"H{row}"] = data.get("Date")
                # Add the image filename for reference in column I
                if "image_filename" in data:
                    sheet[f"I{row}"] = data.get("image_filename")
            
            # Save the workbook
            workbook.save(EXCEL_OUTPUT)
            logger.info(f"Successfully saved data to {EXCEL_OUTPUT} based on template")
            
        else:
            # No template, create a new Excel file
            logger.warning(f"No template found at {EXCEL_TEMPLATE}, creating new Excel file")
            # Create a DataFrame with PatientName, Age, Sex, CardNumber, Telephone, Address, Kebele, Date and image_filename columns
            simplified_data = []
            for item in data_list:
                simplified_data.append({
                    "Patient Name": item.get("PatientName"),
                    "Age": item.get("Age"),
                    "Sex": item.get("Sex"),
                    "Card Number": item.get("CardNumber"),
                    "Telephone": item.get("Telephone"),
                    "Address": item.get("Address"),
                    "Kebele": item.get("Kebele"),
                    "Date": item.get("Date"),
                    "Image Filename": item.get("image_filename", "")
                })
            df = pd.DataFrame(simplified_data)
            df.to_excel(EXCEL_OUTPUT, index=False)
            logger.info(f"Successfully saved data to {EXCEL_OUTPUT}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving to Excel: {str(e)}")
        return False 
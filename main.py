import os
import time
from image_handler import get_image_files, encode_image
from api_handler import extract_text_from_image
from data_parser import parse_extraction_result, validate_data
from excel_handler import save_to_excel
from logger import get_logger

logger = get_logger(__name__)

def process_image(image_path):
    """
    Process a single image through the entire pipeline.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: Extracted data or None if failed
    """
    try:
        # Step 1: Encode the image
        logger.info(f"Processing image: {image_path}")
        base64_image = encode_image(image_path)
        if not base64_image:
            logger.error(f"Failed to encode image: {image_path}")
            return None
        
        # Step 2: Extract text from the image
        extracted_text = extract_text_from_image(base64_image)
        if not extracted_text:
            logger.error(f"Failed to extract text from image: {image_path}")
            return None
        
        # Step 3: Parse the extracted text
        parsed_data = parse_extraction_result(extracted_text)
        if not parsed_data or (parsed_data.get("PatientName") is None and parsed_data.get("Age") is None and 
                              parsed_data.get("Sex") is None and parsed_data.get("CardNumber") is None and 
                              parsed_data.get("Telephone") is None and parsed_data.get("Address") is None and 
                              parsed_data.get("Kebele") is None and parsed_data.get("Date") is None):
            logger.error(f"Failed to parse extraction result for image: {image_path}")
            return None
        
        # Step 4: Validate the parsed data
        is_valid, messages = validate_data(parsed_data)
        if not is_valid:
            logger.warning(f"Data validation issues for {image_path}: {', '.join(messages)}")
            # We'll still return the data even if not valid, but with a warning
        
        # Add the image filename for reference
        parsed_data['image_filename'] = os.path.basename(image_path)
        
        logger.info(f"Successfully processed image: {image_path}")
        logger.info(f"Extracted data: PatientName={parsed_data.get('PatientName')}, Age={parsed_data.get('Age')}, Sex={parsed_data.get('Sex')}, "
                   f"CardNumber={parsed_data.get('CardNumber')}, Telephone={parsed_data.get('Telephone')}, "
                   f"Address={parsed_data.get('Address')}, Kebele={parsed_data.get('Kebele')}, "
                   f"Date={parsed_data.get('Date')}")
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        return None

def main():
    """Main function to process all images and save results to Excel."""
    try:
        logger.info("Starting medical card data extraction")
        
        # Step 1: Get all image files
        image_files = get_image_files()
        if not image_files:
            logger.warning("No image files found to process")
            return
        
        # Step 2: Process each image
        results = []
        for i, image_path in enumerate(image_files):
            logger.info(f"Processing image {i+1}/{len(image_files)}: {image_path}")
            
            # Process the image
            result = process_image(image_path)
            if result:
                results.append(result)
            
            # Add a small delay to avoid rate limiting (optional)
            if i < len(image_files) - 1:
                time.sleep(1)
        
        # Step 3: Save results to Excel
        if results:
            logger.info(f"Saving {len(results)} results to Excel")
            save_to_excel(results)
            logger.info("Medical card data extraction completed successfully")
        else:
            logger.warning("No data extracted from any images")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    main() 
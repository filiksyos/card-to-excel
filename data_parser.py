import json
import re
from logger import get_logger

logger = get_logger(__name__)

def parse_extraction_result(extraction_text):
    """
    Parse the text extracted from the API response into structured data.
    
    Args:
        extraction_text (str): Text extracted from the API response
        
    Returns:
        dict: Structured data with extracted fields
    """
    try:
        logger.debug(f"Parsing extraction result: '{extraction_text}'")
        
        # First, try to extract age from XML tags if present
        age_pattern = r'<age>(.*?)</age>'
        age_match = re.search(age_pattern, extraction_text, re.DOTALL)
        
        if age_match:
            age_value = age_match.group(1).strip()
            logger.info(f"Successfully extracted age from XML tags: {age_value}")
            return {"Age": age_value}
            
        # If the response is just a number, use that directly
        if extraction_text.strip().isdigit():
            age_value = extraction_text.strip()
            logger.info(f"Extracted age as direct number: {age_value}")
            return {"Age": age_value}
            
        # Try to find age mentioned in more flexible formats
        # Look for age patterns in the text
        age_patterns = [
            r'age[:\s]*(\d+)',  # Common pattern: "age: 42" or "age 42"
            r'(\d+)[\s]*(?:years|year|yrs|yr)[\s]*old',  # Patterns like "42 years old"
            r'(\d+)[\s]*(?:years|year|yrs|yr)',  # Patterns like "42 years"
            r'age[:\s]*is[\s]*(\d+)',  # Pattern like "age is 42"
            r'(?:patient|person)[\s]*is[\s]*(\d+)[\s]*(?:years|year|yrs|yr)',  # "patient is 42 years"
            r'(?:patient|person)[\s]*(?:age|aged)[\s]*(\d+)',  # "patient aged 42"
            r'(\d+)[\s]*(?:yo|y\.o\.)',  # Patterns like "42 yo" or "42 y.o."
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, extraction_text, re.IGNORECASE)
            if match:
                age_value = match.group(1).strip()
                logger.info(f"Extracted age using pattern '{pattern}': {age_value}")
                return {"Age": age_value}
                
        # If we've reached here, we couldn't find any age
        logger.warning(f"Could not extract age from text: '{extraction_text}'")
        
        # As a last resort, look for any number in the response
        number_match = re.search(r'(\d+)', extraction_text)
        if number_match:
            potential_age = number_match.group(1)
            if 0 < int(potential_age) < 120:  # Reasonable age range
                logger.info(f"Extracted potential age as fallback: {potential_age}")
                return {"Age": potential_age}
                
        logger.error("Failed to extract any potential age value")
        return {"Age": None}
        
    except Exception as e:
        logger.error(f"Error parsing extraction result: {str(e)}")
        return {"Age": None}

def validate_data(data):
    """
    Validate the extracted data.
    
    Args:
        data (dict): Extracted data
        
    Returns:
        tuple: (is_valid, messages)
    """
    is_valid = True
    messages = []
    
    # Check if age was extracted
    if not data.get("Age"):
        is_valid = False
        messages.append("Age not found in the extracted data")
    else:
        # Validate that age is a number
        try:
            age = data.get("Age")
            if not age.isdigit():
                is_valid = False
                messages.append(f"Age value is not a valid number: {age}")
            else:
                # Check if age is in a reasonable range
                age_int = int(age)
                if age_int <= 0 or age_int >= 120:
                    is_valid = False
                    messages.append(f"Age value {age_int} is outside reasonable range")
        except:
            is_valid = False
            messages.append("Age value could not be validated")
    
    # Log validation results
    if is_valid:
        logger.info("Data validation passed")
    else:
        logger.warning(f"Data validation failed: {', '.join(messages)}")
    
    return is_valid, messages 
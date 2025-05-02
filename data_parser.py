import json
import re
from logger import get_logger

logger = get_logger(__name__)

def normalize_address(address):
    """
    Normalize address, handling special cases like Bahir Dar variations.
    
    Args:
        address (str): Raw address string
        
    Returns:
        str: Normalized address
    """
    if not address:
        return address
        
    # Convert to lowercase for case-insensitive matching
    address_lower = address.lower().strip()
    
    # Check for Bahir Dar variations
    bahir_dar_patterns = [
        r'\bbdr\b', 
        r'\bb/dar\b', 
        r'\bb/dr\b', 
        r'\bbahir\s*dar\b',
        r'\bbahirdar\b'
    ]
    
    for pattern in bahir_dar_patterns:
        if re.search(pattern, address_lower):
            return "Bahir Dar"
    
    # If it's not a variation of Bahir Dar, return the original with proper capitalization
    return address.strip()

def validate_kebele(kebele):
    """
    Validate if a kebele value is valid (01-17 or blank).
    
    Args:
        kebele (str): Kebele value to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Kebele can be blank
    if not kebele or kebele.strip() == "":
        return True
    
    # Extract only numeric characters before checking
    kebele_numeric = ''.join(c for c in kebele if c.isdigit())
    
    # Kebele must be a 2-digit number from 01-17
    try:
        # Check if it's a 2-digit string
        if not re.match(r'^\d{2}$', kebele_numeric):
            return False
        
        # Convert to integer and check range
        kebele_int = int(kebele_numeric)
        return 1 <= kebele_int <= 17
    except:
        return False

def validate_ethiopian_date(date_str):
    """
    Validate if a date string is in valid Ethiopian date format (DD/MM/YYYY).
    
    Args:
        date_str (str): Date string to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not date_str:
        return False
        
    # Check format DD/MM/YYYY
    if not re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        return False
        
    try:
        # Split date components
        day, month, year = date_str.split('/')
        day, month, year = int(day), int(month), int(year)
        
        # Basic validation for date components
        if not (1 <= day <= 30 and 1 <= month <= 13 and 1000 <= year <= 9999):
            # Ethiopian calendar has 30 days per month with 13 months (12 of 30 days, 1 of 5-6 days)
            # Allow for Pagume (13th month)
            return False
            
        # Special case for the 13th month (Pagume) which has 5 or 6 days
        if month == 13 and day > 6:
            return False
            
        return True
    except:
        return False

def normalize_ethiopian_date(date_str):
    """
    Normalize an Ethiopian date string to ensure consistent DD/MM/YYYY format.
    
    Args:
        date_str (str): Date string to normalize
        
    Returns:
        str: Normalized date string
    """
    if not date_str:
        return date_str
        
    # If already in correct format, return as is
    if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_str):
        # Try to ensure day and month are two digits
        try:
            day, month, year = date_str.split('/')
            day = day.zfill(2)  # Pad with leading zero if needed
            month = month.zfill(2)  # Pad with leading zero if needed
            return f"{day}/{month}/{year}"
        except:
            return date_str
            
    return date_str

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
        
        result = {"PatientName": None, "Age": None, "Sex": None, "Telephone": None, "Kebele": None, "Date": None}
        
        # First, try to extract patient_name, age, sex, telephone, kebele, and date from XML tags if present
        patient_name_pattern = r'<patient_name>(.*?)</patient_name>'
        age_pattern = r'<age>(.*?)</age>'
        sex_pattern = r'<sex>(.*?)</sex>'
        telephone_pattern = r'<telephone>(.*?)</telephone>'
        kebele_pattern = r'<kebele>(.*?)</kebele>'
        date_pattern = r'<date>(.*?)</date>'
        
        # Extract patient name
        patient_name_match = re.search(patient_name_pattern, extraction_text, re.DOTALL)
        if patient_name_match:
            patient_name_value = patient_name_match.group(1).strip()
            logger.info(f"Successfully extracted patient name from XML tags: {patient_name_value}")
            result["PatientName"] = patient_name_value
            
        # Extract age
        age_match = re.search(age_pattern, extraction_text, re.DOTALL)
        if age_match:
            age_value = age_match.group(1).strip()
            logger.info(f"Successfully extracted age from XML tags: {age_value}")
            result["Age"] = age_value
            
        # Extract sex
        sex_match = re.search(sex_pattern, extraction_text, re.DOTALL)
        if sex_match:
            sex_value = sex_match.group(1).strip()
            # Ensure sex is either "M" or "F"
            if sex_value in ["M", "F"]:
                logger.info(f"Successfully extracted sex from XML tags: {sex_value}")
                result["Sex"] = sex_value
            else:
                logger.warning(f"Extracted sex value '{sex_value}' is not 'M' or 'F', ignoring")
        
        # Extract telephone number
        telephone_match = re.search(telephone_pattern, extraction_text, re.DOTALL)
        if telephone_match:
            telephone_value = telephone_match.group(1).strip()
            # Ensure telephone number is exactly 10 digits
            if re.match(r'^\d{10}$', telephone_value):
                logger.info(f"Successfully extracted telephone number from XML tags: {telephone_value}")
                result["Telephone"] = telephone_value
            else:
                logger.warning(f"Extracted telephone number '{telephone_value}' is not 10 digits, ignoring")
        
        # Extract kebele
        kebele_match = re.search(kebele_pattern, extraction_text, re.DOTALL)
        if kebele_match:
            kebele_value = kebele_match.group(1).strip()
            # Extract only numbers from kebele value
            kebele_numeric = ''.join(c for c in kebele_value if c.isdigit())
            # Kebele can be blank or a 2-digit number from 01-17
            if kebele_numeric == "" or validate_kebele(kebele_numeric):
                logger.info(f"Successfully extracted kebele from XML tags: '{kebele_numeric}' (from original: '{kebele_value}')")
                result["Kebele"] = kebele_numeric
            else:
                logger.warning(f"Extracted kebele '{kebele_numeric}' (from original: '{kebele_value}') is not valid (must be 01-17 or blank), ignoring")
        
        # Extract date
        date_match = re.search(date_pattern, extraction_text, re.DOTALL)
        if date_match:
            date_value = date_match.group(1).strip()
            if date_value:
                # Validate that it's a valid day (1-30)
                try:
                    day = int(date_value)
                    if 1 <= day <= 30:
                        logger.info(f"Successfully extracted day from date: {day}")
                        result["Date"] = str(day)
                    else:
                        logger.warning(f"Extracted day '{day}' is not in valid range (1-30)")
                except ValueError:
                    logger.warning(f"Extracted date value '{date_value}' is not a valid number")
            else:
                logger.warning("Extracted date is empty, ignoring")
        
        # If any field is extracted, return the result
        if (result["PatientName"] is not None or result["Age"] is not None or result["Sex"] is not None or 
            result["Telephone"] is not None or result["Kebele"] is not None or result["Date"] is not None):
            return result
            
        # Try fallback methods for missing fields
        
        # Patient name fallback methods if not found
        if result["PatientName"] is None:
            # Look for name patterns
            name_patterns = [
                r'(?:name|patient name|full name)[:\s]*([\w\s]+)',  # "name: John Doe" patterns
                r'(?:patient|person)[\s]*(?:is|named)[\s]*([\w\s]+)',  # "patient is John Doe" patterns
                r'\b([A-Za-z]+\s+[A-Za-z]+)\b',  # Basic two-word name pattern
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, extraction_text, re.IGNORECASE)
                if match:
                    name_value = match.group(1).strip()
                    # Check if it looks like a two-word name
                    name_parts = name_value.split()
                    if len(name_parts) == 2:
                        logger.info(f"Extracted patient name using pattern '{pattern}': {name_value}")
                        result["PatientName"] = name_value
                        break
        
        # Age fallback methods if not found
        if result["Age"] is None:
            # If the response is just a number, use that directly
            if extraction_text.strip().isdigit():
                age_value = extraction_text.strip()
                logger.info(f"Extracted age as direct number: {age_value}")
                result["Age"] = age_value
            else:
                # Try to find age mentioned in more flexible formats
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
                        result["Age"] = age_value
                        break
                        
                # As a last resort, look for any number in the response
                if result["Age"] is None:
                    number_match = re.search(r'(\d+)', extraction_text)
                    if number_match:
                        potential_age = number_match.group(1)
                        if 0 < int(potential_age) < 120:  # Reasonable age range
                            logger.info(f"Extracted potential age as fallback: {potential_age}")
                            result["Age"] = potential_age
        
        # Sex fallback methods if not found
        if result["Sex"] is None:
            # Check for Amharic gender characters first
            if "ወ" in extraction_text:
                logger.info("Detected Amharic male character 'ወ', setting sex to 'M'")
                result["Sex"] = "M"
            elif "ሴ" in extraction_text:
                logger.info("Detected Amharic female character 'ሴ', setting sex to 'F'")
                result["Sex"] = "F"
            else:
                # Look for sex/gender mentions
                sex_patterns = [
                    r'\b(male|female)\b',  # Look for "male" or "female"
                    r'\b(M|F)\b',  # Look for "M" or "F"
                    r'(?:sex|gender)[:\s]*(male|female|m|f)',  # "sex: male" or "gender: F"
                    r'(?:patient|person)[\s]*is[\s]*(male|female)'  # "patient is female"
                ]
                
                for pattern in sex_patterns:
                    match = re.search(pattern, extraction_text, re.IGNORECASE)
                    if match:
                        sex_value = match.group(1).strip().upper()
                        # Convert "MALE"/"FEMALE" to "M"/"F"
                        if sex_value == "MALE":
                            sex_value = "M"
                        elif sex_value == "FEMALE":
                            sex_value = "F"
                            
                        # Only accept "M" or "F"
                        if sex_value in ["M", "F"]:
                            logger.info(f"Extracted sex using pattern '{pattern}': {sex_value}")
                            result["Sex"] = sex_value
                            break
        
        # Telephone number fallback if not found
        if result["Telephone"] is None:
            # Look for any 10-digit number (Ethiopian telephone format)
            telephone_patterns = [
                r'\b(\d{10})\b',  # Basic 10-digit pattern
                r'(?:phone|telephone|tel|mobile)[:\s]*(\d{10})',  # "phone: 0912345678" patterns
                r'(?:phone|telephone|tel|mobile)[:\s]*(?:\+251)?(\d{10})',  # Allow for +251 prefix
                r'0(\d{9})'  # Ethiopian pattern starting with 0
            ]
            
            for pattern in telephone_patterns:
                match = re.search(pattern, extraction_text, re.IGNORECASE)
                if match:
                    telephone_value = match.group(1).strip()
                    # Ensure it's 10 digits for Ethiopian format
                    if re.match(r'^\d{10}$', telephone_value) or (
                        re.match(r'^\d{9}$', telephone_value) and pattern == r'0(\d{9})'):
                        # If it's 9 digits from the last pattern, add the leading 0
                        if re.match(r'^\d{9}$', telephone_value) and pattern == r'0(\d{9})':
                            telephone_value = f"0{telephone_value}"
                        logger.info(f"Extracted telephone using pattern '{pattern}': {telephone_value}")
                        result["Telephone"] = telephone_value
                        break
        
        # If we've reached here and couldn't find any fields, log error
        if result["PatientName"] is None:
            logger.error("Failed to extract any potential patient name value")
            
        if result["Age"] is None:
            logger.error("Failed to extract any potential age value")
            
        if result["Sex"] is None:
            logger.error("Failed to extract any potential sex value")
            
        if result["Telephone"] is None:
            logger.error("Failed to extract any potential telephone number value")
            
        if result["Kebele"] is None:
            # Try to extract kebele from text with a focus on numbers only
            kebele_patterns = [
                r'kebele[:\s]*(\d+)', 
                r'(?:district|area|zone)[:\s]*(\d+)',
                r'\bkebele\b[^0-9]*(\d+)',
                r'\bkebele\b[^0-9]*[^\w]*([\d]+)',
                r'(?:ቀ|bdr)[^0-9]*(\d+)'  # Special patterns for kebele with Amharic or abbreviations
            ]
            
            for pattern in kebele_patterns:
                match = re.search(pattern, extraction_text, re.IGNORECASE)
                if match:
                    kebele_value = match.group(1).strip()
                    # Extract only numbers
                    kebele_numeric = ''.join(c for c in kebele_value if c.isdigit())
                    if kebele_numeric and validate_kebele(kebele_numeric):
                        logger.info(f"Extracted kebele using pattern '{pattern}': {kebele_numeric} (from original: '{kebele_value}')")
                        result["Kebele"] = kebele_numeric
                        break
            
            # If still not found, look for any valid-looking kebele number anywhere in the text
            if result["Kebele"] is None:
                # Look for standalone 2-digit numbers that might be kebele
                standalone_numbers = re.findall(r'\b(\d{2})\b', extraction_text)
                for num in standalone_numbers:
                    if validate_kebele(num):
                        logger.info(f"Extracted potential kebele from standalone number: {num}")
                        result["Kebele"] = num
                        break
                        
            if result["Kebele"] is None:
                logger.error("Failed to extract any potential kebele value")
            
        if result["Date"] is None:
            logger.error("Failed to extract any potential date value")
            
        return result
        
    except Exception as e:
        logger.error(f"Error parsing extraction result: {str(e)}")
        return {"PatientName": None, "Age": None, "Sex": None, "Telephone": None, "Kebele": None, "Date": None}

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
    
    # Check if patient name was extracted
    if not data.get("PatientName"):
        is_valid = False
        messages.append("Patient name not found in the extracted data")
    else:
        # Validate that the patient name has at least two words
        patient_name = data.get("PatientName").strip()
        name_parts = patient_name.split()
        if len(name_parts) < 2:
            is_valid = False
            messages.append(f"Patient name '{patient_name}' doesn't contain both first and last name")
    
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
    
    # Check if sex was extracted
    if not data.get("Sex"):
        is_valid = False
        messages.append("Sex not found in the extracted data")
    else:
        # Validate that sex is either "M" or "F"
        sex = data.get("Sex")
        if sex not in ["M", "F"]:
            is_valid = False
            messages.append(f"Sex value '{sex}' is not 'M' or 'F'")
    
    # Check if telephone number was extracted (this field is optional for backward compatibility)
    if data.get("Telephone"):
        # Validate that telephone number is exactly 10 digits
        telephone = data.get("Telephone")
        if not re.match(r'^\d{10}$', telephone):
            is_valid = False
            messages.append(f"Telephone number '{telephone}' is not exactly 10 digits")
        else:
            # Ethiopian telephone numbers typically start with 09
            if not telephone.startswith("09"):
                logger.warning(f"Telephone number '{telephone}' does not start with '09', which is typical for Ethiopian numbers")
    
    # Check if kebele was extracted (this field is optional)
    if data.get("Kebele"):
        # Extract only numbers from kebele value before validation
        kebele = data.get("Kebele")
        kebele_numeric = ''.join(c for c in kebele if c.isdigit())
        
        # Validate that kebele is a 2-digit number from 01-17
        if not validate_kebele(kebele_numeric):
            is_valid = False
            messages.append(f"Kebele '{kebele}' (numeric part: '{kebele_numeric}') is not valid (must be 01-17)")
    
    # Check if date was extracted (this field is optional)
    if data.get("Date"):
        # Validate that date is a number between 1 and 30
        try:
            day = int(data.get("Date"))
            if not (1 <= day <= 30):
                is_valid = False
                messages.append(f"Date '{day}' is not valid (must be between 1 and 30)")
        except ValueError:
            is_valid = False
            messages.append(f"Date '{data.get('Date')}' is not a valid number")
    
    # Log validation results
    if is_valid:
        logger.info("Data validation passed")
    else:
        logger.warning(f"Data validation failed: {', '.join(messages)}")
    
    return is_valid, messages 
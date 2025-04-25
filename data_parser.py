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
    
    # Kebele must be a 2-digit number from 01-17
    try:
        # Check if it's a 2-digit string
        if not re.match(r'^\d{2}$', kebele):
            return False
        
        # Convert to integer and check range
        kebele_int = int(kebele)
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
        
        result = {"PatientName": None, "Age": None, "Sex": None, "Telephone": None, "Address": None, "Kebele": None, "Date": None}
        
        # First, try to extract patient_name, age, sex, telephone, address, kebele, and date from XML tags if present
        patient_name_pattern = r'<patient_name>(.*?)</patient_name>'
        age_pattern = r'<age>(.*?)</age>'
        sex_pattern = r'<sex>(.*?)</sex>'
        telephone_pattern = r'<telephone>(.*?)</telephone>'
        address_pattern = r'<address>(.*?)</address>'
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
        
        # Extract address
        address_match = re.search(address_pattern, extraction_text, re.DOTALL)
        if address_match:
            address_value = address_match.group(1).strip()
            if address_value:
                # Normalize address (handle Bahir Dar variations)
                normalized_address = normalize_address(address_value)
                logger.info(f"Successfully extracted address from XML tags: '{address_value}', normalized to: '{normalized_address}'")
                result["Address"] = normalized_address
            else:
                logger.warning("Extracted address is empty, ignoring")
        
        # Extract kebele
        kebele_match = re.search(kebele_pattern, extraction_text, re.DOTALL)
        if kebele_match:
            kebele_value = kebele_match.group(1).strip()
            # Kebele can be blank or a 2-digit number from 01-17
            if kebele_value == "" or validate_kebele(kebele_value):
                logger.info(f"Successfully extracted kebele from XML tags: '{kebele_value}'")
                result["Kebele"] = kebele_value
            else:
                logger.warning(f"Extracted kebele '{kebele_value}' is not valid (must be 01-17 or blank), ignoring")
        
        # Extract date
        date_match = re.search(date_pattern, extraction_text, re.DOTALL)
        if date_match:
            date_value = date_match.group(1).strip()
            if date_value:
                # Validate and normalize Ethiopian date
                if validate_ethiopian_date(date_value):
                    normalized_date = normalize_ethiopian_date(date_value)
                    logger.info(f"Successfully extracted date from XML tags: '{date_value}', normalized to: '{normalized_date}'")
                    result["Date"] = normalized_date
                else:
                    logger.warning(f"Extracted date '{date_value}' is not in valid Ethiopian format (DD/MM/YYYY), ignoring")
            else:
                logger.warning("Extracted date is empty, ignoring")
        
        # If any field is extracted, return the result
        if (result["PatientName"] is not None or result["Age"] is not None or result["Sex"] is not None or 
            result["Telephone"] is not None or result["Address"] is not None or result["Kebele"] is not None or
            result["Date"] is not None):
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
        
        # Address fallback if not found
        if result["Address"] is None:
            # Look for address mentions
            address_patterns = [
                r'(?:address|location|city|town)[:\s]*([\w\s/]+)',  # "address: Bahir Dar" patterns
                r'(?:from|in|at)[:\s]*([\w\s/]+)',  # "from Bahir Dar" patterns
                r'\b(bahir\s*dar|bdr|b/dar|b/dr)\b',  # Bahir Dar variations
                r'\b(addis\s*ababa|aa|a\.a\.)\b',  # Addis Ababa variations
                r'\b(gondar|gonder)\b',  # Other common Ethiopian cities
                r'\b(hawassa|awassa)\b',
                r'\b(mekelle|mekele)\b',
                r'\b(dire\s*dawa)\b',
                r'\b(dessie|dese)\b',
                r'\b(jimma|jima)\b',
                r'\b(debre\s*birhan)\b',
                r'\b(debre\s*markos)\b',
                r'\b(woldia|woldiya)\b'
            ]
            
            for pattern in address_patterns:
                match = re.search(pattern, extraction_text, re.IGNORECASE)
                if match:
                    address_value = match.group(1).strip()
                    normalized_address = normalize_address(address_value)
                    logger.info(f"Extracted address using pattern '{pattern}': '{address_value}', normalized to: '{normalized_address}'")
                    result["Address"] = normalized_address
                    break
        
        # Kebele fallback if not found
        if result["Kebele"] is None:
            # Look for kebele mentions
            kebele_patterns = [
                r'(?:kebele|keb)[:\s]*(\d{1,2})',  # "kebele: 05" patterns
                r'(?:kebele|keb)[\s]*#?(\d{1,2})',  # "kebele #5" patterns
                r'(?:district|dist)[:\s]*(\d{1,2})',  # "district: 05" patterns
                r'\bkeb\.?\s*(\d{1,2})\b',  # "keb. 5" patterns
            ]
            
            for pattern in kebele_patterns:
                match = re.search(pattern, extraction_text, re.IGNORECASE)
                if match:
                    kebele_value = match.group(1).strip()
                    
                    # If it's a single digit, pad with leading zero
                    if re.match(r'^\d$', kebele_value):
                        kebele_value = f"0{kebele_value}"
                    
                    if validate_kebele(kebele_value):
                        logger.info(f"Extracted kebele using pattern '{pattern}': '{kebele_value}'")
                        result["Kebele"] = kebele_value
                        break
                    else:
                        logger.warning(f"Extracted kebele '{kebele_value}' is not valid (must be 01-17)")
        
        # Date fallback if not found
        if result["Date"] is None:
            # Look for date mentions
            date_patterns = [
                r'(?:date)[:\s]*(\d{1,2}/\d{1,2}/\d{4})',  # "date: 12/03/2012" patterns
                r'(\d{1,2}/\d{1,2}/\d{4})',  # Basic DD/MM/YYYY pattern
                r'(\d{1,2}-\d{1,2}-\d{4})',  # DD-MM-YYYY pattern (convert to DD/MM/YYYY)
                r'(\d{1,2}\.\d{1,2}\.\d{4})',  # DD.MM.YYYY pattern (convert to DD/MM/YYYY)
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, extraction_text, re.IGNORECASE)
                if match:
                    date_value = match.group(1).strip()
                    
                    # Convert alternative formats to DD/MM/YYYY
                    if "-" in date_value:
                        date_value = date_value.replace("-", "/")
                    if "." in date_value:
                        date_value = date_value.replace(".", "/")
                    
                    if validate_ethiopian_date(date_value):
                        normalized_date = normalize_ethiopian_date(date_value)
                        logger.info(f"Extracted date using pattern '{pattern}': '{date_value}', normalized to: '{normalized_date}'")
                        result["Date"] = normalized_date
                        break
                    else:
                        logger.warning(f"Extracted date '{date_value}' is not valid (must be DD/MM/YYYY in Ethiopian calendar)")
        
        # If we've reached here and couldn't find any fields, log error
        if result["PatientName"] is None:
            logger.error("Failed to extract any potential patient name value")
            
        if result["Age"] is None:
            logger.error("Failed to extract any potential age value")
            
        if result["Sex"] is None:
            logger.error("Failed to extract any potential sex value")
            
        if result["Telephone"] is None:
            logger.error("Failed to extract any potential telephone number value")
            
        if result["Address"] is None:
            logger.error("Failed to extract any potential address value")
            
        # Kebele and Date are optional, so we don't log an error if they're not found
            
        return result
        
    except Exception as e:
        logger.error(f"Error parsing extraction result: {str(e)}")
        return {"PatientName": None, "Age": None, "Sex": None, "Telephone": None, "Address": None, "Kebele": None, "Date": None}

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
        # Validate that kebele is a 2-digit number from 01-17
        kebele = data.get("Kebele")
        if not validate_kebele(kebele):
            is_valid = False
            messages.append(f"Kebele '{kebele}' is not valid (must be 01-17)")
    
    # Check if date was extracted (this field is optional)
    if data.get("Date"):
        # Validate that date is in DD/MM/YYYY format for Ethiopian calendar
        date = data.get("Date")
        if not validate_ethiopian_date(date):
            is_valid = False
            messages.append(f"Date '{date}' is not valid (must be DD/MM/YYYY in Ethiopian calendar)")
    
    # Log validation results
    if is_valid:
        logger.info("Data validation passed")
    else:
        logger.warning(f"Data validation failed: {', '.join(messages)}")
    
    return is_valid, messages 
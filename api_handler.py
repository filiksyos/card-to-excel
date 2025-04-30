import requests
import time
import json
from config import OPENROUTER_API_KEY, OPENROUTER_API_URL, MODEL_NAME
from logger import get_logger

logger = get_logger(__name__)

def extract_text_from_image(base64_image):
    """
    Extract text from an image using OpenRouter API.
    
    Args:
        base64_image (str): Base64 encoded image
        
    Returns:
        str: Extracted text from the image
    """
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key not provided")
        raise ValueError("OpenRouter API key not provided")
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",  # Required for OpenRouter
        "X-Title": "Medical Card Extractor"  # Optional but helpful for analytics
    }
    
    # Updated prompt to extract patient_name, age, sex, telephone, kebele, and date with XML tags
    prompt = """
    This is a medical card. Please extract ONLY the following information from their EXACT locations and ignore everything else in the image:

    1. Patient's name (located in the middle-left of the card, under "Name")
    2. Age (located in the middle of the card, under "Age")
    3. Sex/gender (located in the middle-right of the card, under "Sex" - only respond with "M" for male or "F" for female)
    4. Telephone number (located in the bottom-right of the card, under "Tel. No" - Ethiopian format, exactly 10 digits)
    5. Kebele (located in the bottom-middle of the card, under "Kebele" - 2-digit district number from 01-17, might be blank)
    6. Date (located in the top-right of the card, under "Date" - only extract the day part, e.g. if date is 15/8/2016, extract only 15)

    IMPORTANT LOCATION INSTRUCTIONS:
    - Look for the name field in the middle-left section
    - Look for the age field in the middle section
    - Look for the sex field in the middle-right section
    - Look for the telephone number in the bottom-right corner
    - Look for the kebele number in the bottom-middle section
    - Look for the date in the top-right corner
    
    IGNORE ALL OTHER TEXT AND ELEMENTS IN THE CARD.
    DO NOT extract any other information besides these specific fields from their specific locations.
    
    Format your response exactly like this:
    <patient_name>FIRST_NAME LAST_NAME</patient_name>
    <age>NUMBER</age>
    <sex>M_OR_F</sex>
    <telephone>10_DIGITS</telephone>
    <kebele>2_DIGITS_OR_BLANK</kebele>
    <date>DAY_ONLY</date>
    
    Rules:
    - Only use "M" or "F" for sex (not "Male" or "Female")
    - Telephone number must be exactly 10 digits in Ethiopian format
    - Kebele should be a 2-digit number from 01-17 or left blank if not found
    - Date should be only the day part (1-30) from the date field
    - Extract names exactly as written, preserving Ethiopian naming style
    - Do not include any other text or explanations
    """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in extracting specific information from images. Be concise and direct. Always follow the exact format requested."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300,     # Increased token limit to accommodate all fields
        "temperature": 0.1    # Lower temperature for more deterministic responses
    }
    
    try:
        # Make API request
        logger.info("Sending image to OpenRouter API")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        
        # Log response status and headers
        logger.info(f"API response status: {response.status_code}")
        logger.info(f"API response headers: {dict(response.headers)}")
        
        # Check for rate limiting
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 5))
            logger.warning(f"Rate limited. Retrying after {retry_after} seconds")
            time.sleep(retry_after)
            return extract_text_from_image(base64_image)
        
        # Check for unauthorized error (likely API key issue)
        if response.status_code == 401:
            logger.error("Unauthorized: Check your OpenRouter API key")
            return None
            
        # Log the full response text for debugging
        logger.debug(f"API response text: {response.text}")
        
        # Check for payment required error
        if response.status_code == 402:
            response_data = response.json()
            if 'error' in response_data:
                logger.error(f"API payment error: {response_data['error']['message']}")
            else:
                logger.error("Payment required: Insufficient credits on OpenRouter")
            return None
            
        # Check for successful response
        response.raise_for_status()
        
        # Parse response
        response_data = response.json()
        
        # Log the structure of the response
        logger.debug(f"API response structure: {json.dumps(response_data, indent=2)}")
        
        # Extract content based on the response structure
        try:
            extracted_text = response_data['choices'][0]['message']['content']
            logger.info(f"Successfully extracted text from image: '{extracted_text}'")
            
            # Check if the response already has XML tags
            if "<patient_name>" in extracted_text and "<age>" in extracted_text and "<sex>" in extracted_text:
                return extracted_text
                
            # If not, try to format it with XML tags (fallback methods)
            
            # Look for patient_name, age, sex, telephone, kebele, and date separately
            import re
            
            # For responses without proper formatting
            name_match = re.search(r'\b([A-Za-z]+\s+[A-Za-z]+)\b', extracted_text)
            age_match = re.search(r'\b(\d+)\b', extracted_text)
            sex_match = re.search(r'\b([MF])\b', extracted_text)
            telephone_match = re.search(r'\b(0\d{9})\b', extracted_text)  # Look for 10-digit number starting with 0
            
            # Address, Kebele, and Date will be extracted by the data parser with more complex logic
            
            if name_match and age_match and sex_match:
                name = name_match.group(1)
                age = age_match.group(1)
                sex = sex_match.group(1)
                telephone = telephone_match.group(1) if telephone_match else ""
                
                formatted_response = f"<patient_name>{name}</patient_name>\n<age>{age}</age>\n<sex>{sex}</sex>"
                if telephone:
                    formatted_response += f"\n<telephone>{telephone}</telephone>"
                
                logger.info(f"Formatted response: {formatted_response}")
                return formatted_response
            
            # As a last resort, return the raw text
            return extracted_text
                
        except KeyError as e:
            logger.error(f"Unexpected response structure: {e}")
            logger.error(f"Response data: {response_data}")
            
            # Try alternative keys that might be present
            if 'error' in response_data:
                logger.error(f"API error: {response_data['error']}")
            
            return None
        
    except requests.RequestException as e:
        logger.error(f"API request error: {str(e)}")
        return None
    except (KeyError, IndexError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in API request: {str(e)}")
        return None 
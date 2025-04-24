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
    
    # Simpler prompt for gpt-4o-mini
    prompt = """
    This is a medical card. Please extract ONLY the patient's age from this image.
    
    Respond with the age number only. For example, if the patient is 45 years old, just respond with "45".
    Do not include any other text, explanations, or formatting.
    """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in extracting specific information from images. Be concise and direct."
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
        "max_tokens": 50,     # Reduced token limit since we only need a number
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
            
            # Format the response to be compatible with our parser
            # Wrap the age in XML tags if it's just a number
            if extracted_text.strip().isdigit():
                formatted_response = f"<age>{extracted_text.strip()}</age>"
                logger.info(f"Formatted response: {formatted_response}")
                return formatted_response
            else:
                # Return as is for the parser to handle
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
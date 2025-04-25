import requests
import os
from dotenv import load_dotenv
import base64
from PIL import Image
from io import BytesIO
import json
import re

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv('OPENROUTER_API_KEY')
print(f"API key found: {'Yes' if api_key else 'No'}")

if not api_key:
    print("Please enter your OpenRouter API key: ", end='')
    api_key = input().strip()
    
    # Save to .env file
    with open('.env', 'w') as f:
        f.write(f"OPENROUTER_API_KEY={api_key}\n")
        f.write("IMAGE_DIR=images\n")
        f.write("OUTPUT_DIR=output\n")
        f.write("EXCEL_TEMPLATE=template.xlsx\n")
        f.write("EXCEL_OUTPUT=output/age_extracted_data.xlsx\n")
        f.write("LOG_LEVEL=DEBUG\n")
        f.write("LOG_FILE=app.log\n")
    print("API key saved to .env file")

# Simple test with text prompt
def test_text_api():
    print("\nTesting text API...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "Medical Card Extractor Test"
    }
    
    payload = {
        "model": "openai/gpt-4o-mini",  # Updated to gpt-4o-mini
        "messages": [
            {
                "role": "user",
                "content": "Say hello world"
            }
        ],
        "max_tokens": 50,  # Reduced token limit
        "temperature": 0.1  # Lower temperature for more deterministic responses
    }
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"Response content: {content}")
            else:
                print(f"Unexpected response structure: {json.dumps(data, indent=2)}")
        else:
            print(f"API error: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

# Function to encode an image
def encode_test_image():
    print("\nEncoding test image...")
    try:
        image_files = [f for f in os.listdir('images') if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        if not image_files:
            print("No image files found in 'images' directory")
            return None
            
        image_path = os.path.join('images', image_files[0])
        print(f"Using image: {image_path}")
        
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            
        encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        print(f"Image encoded successfully (length: {len(encoded_image)} characters)")
        return encoded_image
    except Exception as e:
        print(f"Error encoding image: {str(e)}")
        return None

# Test with image
def test_image_api():
    print("\nTesting image API...")
    encoded_image = encode_test_image()
    if not encoded_image:
        return
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://localhost",
        "X-Title": "Medical Card Extractor Test"
    }
    
    # Updated prompt to extract both age and sex
    prompt = """
    This is a medical card. Please extract the following information:
    
    1. Patient's age
    2. Patient's sex/gender (only respond with "M" for male or "F" for female)
    
    Format your response exactly like this:
    <age>NUMBER</age>
    <sex>M_OR_F</sex>
    
    Only use "M" or "F" for sex (not "Male" or "Female").
    Do not include any other text or explanations.
    """
    
    payload = {
        "model": "openai/gpt-4o-mini",  # Updated to gpt-4o-mini
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
                            "url": f"data:image/jpeg;base64,{encoded_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 50,     # Reduced token limit since we only need two short values
        "temperature": 0.1    # Lower temperature for more deterministic responses
    }
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    try:
        print("Sending request to API...")
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response data: {json.dumps(data, indent=2)}")
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                print(f"Response content: {content}")
                
                # Try to parse the age and sex
                try:
                    # Look for XML tags
                    age_match = re.search(r'<age>(.*?)</age>', content)
                    sex_match = re.search(r'<sex>(.*?)</sex>', content)
                    
                    if age_match:
                        print(f"Extracted age: {age_match.group(1)}")
                    else:
                        print("Could not find age in XML format")
                        
                    if sex_match:
                        print(f"Extracted sex: {sex_match.group(1)}")
                    else:
                        print("Could not find sex in XML format")
                        
                    # If XML tags not found, try alternate patterns
                    if not age_match and not sex_match:
                        # Try to find age and sex in other formats
                        age_number = re.search(r'\b(\d+)\b', content)
                        sex_letter = re.search(r'\b([MF])\b', content)
                        
                        if age_number:
                            print(f"Extracted age (alternative): {age_number.group(1)}")
                        
                        if sex_letter:
                            print(f"Extracted sex (alternative): {sex_letter.group(1)}")
                            
                except Exception as e:
                    print(f"Error parsing response: {str(e)}")
            else:
                print(f"Unexpected response structure: {json.dumps(data, indent=2)}")
        else:
            print(f"API error: {response.text}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("OpenRouter API Test")
    print("===================")
    
    # Run tests
    test_text_api()
    test_image_api()
    
    print("\nTest complete!") 
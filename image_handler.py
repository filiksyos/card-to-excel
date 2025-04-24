import os
import base64
from PIL import Image
from io import BytesIO
from config import IMAGE_DIR, SUPPORTED_FORMATS
from logger import get_logger

logger = get_logger(__name__)

def get_image_files():
    """
    Get all supported image files from the image directory.
    
    Returns:
        list: List of image file paths
    """
    image_files = []
    
    # Create image directory if it doesn't exist
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)
        logger.info(f"Created image directory: {IMAGE_DIR}")
        return image_files
    
    # Get all supported image files
    for filename in os.listdir(IMAGE_DIR):
        file_path = os.path.join(IMAGE_DIR, filename)
        if os.path.isfile(file_path):
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext in SUPPORTED_FORMATS:
                image_files.append(file_path)
    
    logger.info(f"Found {len(image_files)} image files")
    return image_files

def encode_image(image_path):
    """
    Encode an image to base64 for API submission.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Base64 encoded image
    """
    try:
        # Open and resize image if needed
        with Image.open(image_path) as img:
            # Convert to RGB if it's not
            if img.mode != 'RGB':
                img = img.convert('RGB')
                
            # Resize if necessary (optional)
            # img = img.resize((800, 600), Image.LANCZOS)
            
            # Save to buffer
            buffer = BytesIO()
            img.save(buffer, format="JPEG")
            
        # Encode to base64
        encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
        logger.info(f"Successfully encoded image: {image_path}")
        return encoded_image
    
    except Exception as e:
        logger.error(f"Error encoding image {image_path}: {str(e)}")
        return None 
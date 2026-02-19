import easyocr
import cv2
import numpy as np
import re
import os

# Initialize Reader once (it loads model into memory)
# 'en' for English. GPU=False for compatibility if no CUDA.
reader = easyocr.Reader(['en'], gpu=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

def process_prescription_image(image_path):
    """
    Reads image, preprocesses it, runs OCR, and extracts optical details.
    """
    try:
        # 1. Read Image
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Could not read image"}

        # 2. Preprocessing (Grayscale + Thresholding)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Apply simple thresholding to clear noise
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 3. Run EasyOCR
        # detail=0 returns just the list of text strings
        results = reader.readtext(thresh, detail=0)
        
        # 4. Parse Text
        extracted_data = parse_ocr_text(results)
        
        return extracted_data
    except Exception as e:
        return {"error": str(e)}

def parse_ocr_text(text_list):
    """
    Heuristic parser to find Right Eye (OD/RE) and Left Eye (OS/LE) values.
    Looks for patterns like SPH, CYL, AXIS or just numbers following OD/OS keys.
    """
    full_text = " ".join(text_list).upper()
    
    data = {
        "re_sph": None, "re_cyl": None, "re_axis": None,
        "le_sph": None, "le_cyl": None, "le_axis": None
    }

    # Regex for finding diopter values (e.g., -1.25, +2.00, 0.50)
    # Allows optional +/-, digits, optional decimal
    number_pattern = r'[+-]?\d+(?:\.\d{2})?' 
    
    # 1. Try to find explicit blocks for RE/OD and LE/OS
    # This is hard because OCR flattens layout. 
    # We will look for sequences of numbers near keywords.

    # Heuristic: Find "SPH" and look for nearest numbers?
    # Or find "OD" (Right) and "OS" (Left) lines.
    
    # Let's try iterating through lines to find "OD" or "R" and "OS" or "L"
    
    # Simple strategy: Find all numbers with decimals (likely SPH/CYL) and integers (AXIS)
    # This is very prone to error without fixed forms. 
    # We will assume a standard sequence: SPH -> CYL -> AXIS if multiple numbers appear.
    
    # Let's try to detect if we have specific labels
    tokens = full_text.split()
    
    # Temporary storage for found numbers
    numbers = [t for t in tokens if re.match(r'^[+-]?\d+(\.\d+)?$', t)]
    
    # If we found at least 6 numbers, maybe they are RE SPH, CYL, AXIS, LE SPH, CYL, AXIS
    # This is a wild guess but better than nothing for a basic V1
    if len(numbers) >= 6:
        data["re_sph"] = numbers[0]
        data["re_cyl"] = numbers[1]
        data["re_axis"] = numbers[2]
        data["le_sph"] = numbers[3]
        data["le_cyl"] = numbers[4]
        data["le_axis"] = numbers[5]
    
    return data

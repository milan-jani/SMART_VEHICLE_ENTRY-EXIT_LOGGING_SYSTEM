"""
Azure Computer Vision OCR Module
Extracts details from ID cards (Aadhaar, PAN, DL) using Azure Computer Vision v3.2.
"""
import os
import time
import requests
import re

from app.device.config import AZURE_CV_ENDPOINT, AZURE_CV_KEY

def extract_id_details(image_path: str, side: str = "front") -> dict:
    """
    Sends the image to Azure Computer Vision Read API and extracts text details.
    """
    if not AZURE_CV_ENDPOINT or not AZURE_CV_KEY:
        return {"error": "Azure Computer Vision not configured"}
        
    full_image_path = os.path.abspath(image_path)
    if not os.path.exists(full_image_path):
        return {"error": f"Image file not found: {image_path}"}
        
    # Azure v3.2 Read endpoint
    analyze_url = f"{AZURE_CV_ENDPOINT.rstrip('/')}/vision/v3.2/read/analyze"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_CV_KEY,
        'Content-Type': 'application/octet-stream'
    }
    
    try:
        # Step 1: Submit image to Azure
        with open(full_image_path, "rb") as image_data:
            response = requests.post(analyze_url, headers=headers, data=image_data)
            
        if response.status_code not in [200, 202]:
            return {"error": f"Azure API Error: {response.text}"}
            
        operation_url = response.headers.get("Operation-Location")
        if not operation_url:
            return {"error": "No operation location received from Azure"}
            
        # Step 2: Poll for results
        poll_headers = {'Ocp-Apim-Subscription-Key': AZURE_CV_KEY}
        max_retries = 15
        ocr_result = None
        
        for _ in range(max_retries):
            time.sleep(1.0)
            poll_resp = requests.get(operation_url, headers=poll_headers)
            poll_resp.raise_for_status()
            
            result_json = poll_resp.json()
            if result_json.get("status") == "succeeded":
                ocr_result = result_json
                break
            elif result_json.get("status") == "failed":
                return {"error": "Azure OCR processing failed"}
                
        if not ocr_result:
            return {"error": "OCR polling timed out"}
            
        # Step 3: Extract lines
        lines = []
        read_results = ocr_result.get("analyzeResult", {}).get("readResults", [])
        if read_results:
            for line in read_results[0].get("lines", []):
                lines.append(line.get("text", "").strip())
                
        if not lines:
            return {"error": "No text detected in image"}
            
        # Process extracted text
        if side == "front":
            return parse_front_id(lines)
        else:
            return parse_back_id(lines)
            
    except Exception as e:
        return {"error": f"OCR extraction error: {str(e)}"}

def parse_front_id(lines: list) -> dict:
    """Extracts Name, ID number, and DOB from front side text lines."""
    result = {
        "name": "",
        "id_number": "",
        "dob": "",
        "confidence": 0.82  # Assuming high confidence from Azure MS OCR
    }
    
    # Regex patterns
    aadhaar_pattern = r'\b(\d{4}[\s-]?\d{4}[\s-]?\d{4})\b'
    pan_pattern = r'\b([A-Z]{5}[0-9]{4}[A-Z])\b'
    dl_pattern = r'\b([A-Z]{2}[0-9]{2}[\s-]?[0-9]{11})\b'
    voter_pattern = r'\b([A-Z]{3}[0-9]{7})\b'
    dob_pattern = r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b'
    
    name_candidates = []
    
    for line in lines:
        text = line.upper()
        
        # Skip common headings
        if any(w in text for w in ["GOVT", "GOVERNMENT", "INDIA", "DEPARTMENT", "DRIVING", "LICENCE", "LICENSE", "ELECTION", "COMMISSION", "FATHER"]):
            continue
            
        # ID Numbers
        if not result["id_number"]:
            if m := re.search(aadhaar_pattern, text):
                result["id_number"] = m.group(1).replace("-", " ")
                continue
            if m := re.search(pan_pattern, text):
                result["id_number"] = m.group(1)
                continue
            if m := re.search(dl_pattern, text):
                result["id_number"] = m.group(1)
                continue
            if m := re.search(voter_pattern, text):
                result["id_number"] = m.group(1)
                continue
                
        # DOB
        if not result["dob"]:
            if m := re.search(dob_pattern, text):
                d_str = m.group(1).replace("/", "-")
                parts = d_str.split("-")
                # Format to YYYY-MM-DD for HTML input[type=date]
                if len(parts) == 3 and len(parts[2]) == 4:
                    result["dob"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else:
                    result["dob"] = d_str
                continue
                
        # Name heuritics: All caps, mostly alphabets, 2+ words
        if re.match(r'^[A-Z][A-Z\s]+$', text) and len(text) > 4 and len(text.split()) >= 2:
            name_candidates.append(line.title())
            
    # Typically first valid name candidate is the person's name
    if name_candidates:
        result["name"] = name_candidates[0]
        
    return result

def parse_back_id(lines: list) -> dict:
    """Extracts Address (street, city, state) from back side text lines."""
    result = {
        "address_street": "",
        "address_city": "",
        "address_state": "",
        "confidence": 0.82
    }
    
    address_lines = []
    capture = False
    
    for line in lines:
        text = line.upper()
        
        if any(marker in text for marker in ["ADDRESS", "ADD:", "W/O", "S/O", "D/O", "C/O"]):
            capture = True
            parts = re.split(r'ADDRESS:|ADD:|W/O|S/O|D/O|C/O', text)
            if len(parts) > 1 and len(parts[-1].strip()) > 2:
                address_lines.append(parts[-1].strip().title())
            continue
            
        if capture:
            if re.search(r'\b\d{6}\b', text):
                address_lines.append(line.title())
                capture = False # Pin code usually marks end
            elif len(text) > 3:
                address_lines.append(line.title())
                
    if not address_lines:
        valid_lines = [l.title() for l in lines if len(l) > 10 and not re.search(r'^[0-9]+$', l)]
        address_lines = valid_lines
        
    full_address = ", ".join(address_lines)
    
    if full_address:
        parts = full_address.split(",")
        if len(parts) >= 3:
            result["address_state"] = parts[-1].strip()
            city_str = parts[-2].strip()
            result["address_city"] = re.sub(r'\b\d{6}\b', '', city_str).strip()
            result["address_street"] = ", ".join(parts[:-2]).strip()
        else:
            result["address_street"] = full_address
            
    return result

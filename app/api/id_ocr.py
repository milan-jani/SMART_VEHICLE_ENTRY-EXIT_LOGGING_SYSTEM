"""
Azure Computer Vision OCR Module
Extracts details from ID cards (Aadhaar, PAN, DL) using Azure Computer Vision v3.2.
Supports: Aadhaar Card, Driving License (DL), PAN Card, Voter ID

Uses unified label-aware parsing that works regardless of front/back side.
"""
import os
import time
import requests
import re

from app.device.config import AZURE_CV_ENDPOINT, AZURE_CV_KEY


def extract_id_details(image_path: str, side: str = "front") -> dict:
    """
    Sends the image to Azure Computer Vision Read API and extracts text details.
    Uses unified smart parsing that works for Aadhaar, DL, PAN, etc.
    Returns ALL fields (name, id, dob, phone, address) regardless of 'side'.
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
            print(f"[ERROR] Azure OCR API Error: {response.status_code} - {response.text}")
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
        
        # Debug: log raw OCR lines in terminal
        print(f"[OCR] Raw lines detected ({len(lines)}):")
        for i, line in enumerate(lines):
            print(f"  {i+1}. {line}")
            
        # Detect document type and extract all fields
        doc_type = _detect_document_type(lines)
        print(f"[OCR] Detected document type: {doc_type}")
        
        result = _extract_all_fields(lines, doc_type)
        
        print(f"[OCR] Extracted: name='{result.get('name')}', id='{result.get('id_number')}', "
              f"dob='{result.get('dob')}', phone='{result.get('phone')}', "
              f"address='{result.get('address')}'")
        
        return result
            
    except Exception as e:
        print(f"[ERROR] OCR extraction error: {str(e)}")
        return {"error": f"OCR extraction error: {str(e)}"}


# ─────────────────────────────────────────────────────────────
#  Document Type Detection
# ─────────────────────────────────────────────────────────────

def _detect_document_type(lines):
    """Detect if the document is Aadhaar, DL, PAN, Voter ID, etc."""
    full_text = " ".join(lines).upper()
    
    if "DRIVING" in full_text and ("LICENCE" in full_text or "LICENSE" in full_text):
        return "DL"
    if any(w in full_text for w in ["AADHAAR", "UIDAI", "UNIQUE IDENTIFICATION"]):
        return "AADHAAR"
    if any(w in full_text for w in ["INCOME TAX", "PERMANENT ACCOUNT"]):
        return "PAN"
    if any(w in full_text for w in ["ELECTION", "VOTER", "NIRVACHAN"]):
        return "VOTER"
    
    # Detect by ID number patterns if header text not found
    for line in lines:
        text = line.upper()
        if re.search(r'\b[A-Z]{2}\d{2}\s?\d{11,13}\b', text):
            return "DL"
        if re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', text):
            return "AADHAAR"
        if re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', text):
            return "PAN"
    
    return "UNKNOWN"


# ─────────────────────────────────────────────────────────────
#  Universal Field Extractor
# ─────────────────────────────────────────────────────────────

def _extract_all_fields(lines, doc_type):
    """
    Universal field extractor for Indian ID documents.
    Returns a single 'address' field (not split into street/city/state).
    """
    result = {
        "name": "",
        "id_number": "",
        "dob": "",
        "phone": "",
        "address": "",
        "confidence": 0.82
    }
    
    _extract_id_number(lines, result)
    _extract_name(lines, result, doc_type)
    _extract_dob(lines, result, doc_type)
    _extract_address_and_phone(lines, result, doc_type)
    
    return result


def _extract_id_number(lines, result):
    """Extract ID number (DL, Aadhaar, PAN, Voter ID)."""
    for line in lines:
        if result["id_number"]:
            break
        text = line.upper().strip()
        
        # DL number: GJ25 20230003704
        m = re.search(r'\b([A-Z]{2}\d{2}\s?\d{11,13})\b', text)
        if m:
            result["id_number"] = m.group(1)
            continue
        
        # Aadhaar: 9218 5218 0131 (skip VID lines)
        if "VID" not in text:
            m = re.search(r'\b(\d{4}\s\d{4}\s\d{4})\b', text)
            if m:
                result["id_number"] = m.group(1)
                continue
        
        # PAN: ABCDE1234F
        m = re.search(r'\b([A-Z]{5}\d{4}[A-Z])\b', text)
        if m:
            result["id_number"] = m.group(1)
            continue
        
        # Voter ID: ABC1234567
        m = re.search(r'\b([A-Z]{3}\d{7})\b', text)
        if m:
            result["id_number"] = m.group(1)
            continue


def _extract_name(lines, result, doc_type):
    """Extract person's name — label-based first, then heuristic fallback."""
    
        # Strategy 1: Label-based (DL style: "Name : YEDUNANDAN S NAMBIAR" or "Name YEDUNANDAN")
    for line in lines:
        upper = line.upper().strip()
        
        m = re.match(r'NAME\s*[:：]?\s+(.+)', upper)
        if m:
            name_val = m.group(1).strip()
            # Remove "Holder's Signature" noise from right side of DL
            name_val = re.sub(r"HOLDER.*", "", name_val, flags=re.IGNORECASE).strip()
            # Keep only letters and spaces
            name_val = re.sub(r"[^A-Za-z\s]", "", name_val).strip()
            if len(name_val) > 2:
                result["name"] = name_val.title()
            return
    
    # Strategy 2: Heuristic fallback (Aadhaar style — clean alphabetic line)
    SKIP_WORDS = {
        "GOVERNMENT", "INDIA", "AADHAAR", "MALE", "FEMALE", "DOB", "VID",
        "ISSUE", "DRIVING", "LICENCE", "LICENSE", "UNION", "UNIQUE",
        "IDENTIFICATION", "AUTHORITY", "ELECTION", "COMMISSION",
        "HOLDER", "SIGNATURE", "BLOOD", "GROUP", "ORGAN", "DONOR",
        "SON", "DAUGHTER", "WIFE", "VALIDITY", "INCOME", "TAX",
        "DEPARTMENT", "PERMANENT", "ACCOUNT", "ADDRESS", "ADD",
        "TRANSPORT", "STATE", "ISSUED", "DATE", "BIRTH", "FATHER",
        "HUSBAND", "REPUBLIC", "GUJARAT", "MAHARASHTRA", "RAJASTHAN",
        "DELHI", "KARNATAKA", "TAMIL", "BENGAL", "PRADESH", "KERALA",
        "PUNJAB", "HARYANA", "MADHYA", "UTTAR", "BIHAR", "ODISHA",
    }
    
    for line in lines:
        text = line.strip()
        upper = text.upper()
        
        # Skip if any skip word is present
        words_in_line = set(upper.split())
        if words_in_line & SKIP_WORDS:
            continue
        # Skip non-ASCII (Gujarati, Hindi, etc.)
        if any(ord(c) > 127 for c in text):
            continue
        # Skip lines containing digits
        if re.search(r'\d', text):
            continue
        # Skip very short lines
        if len(text) <= 4:
            continue
        # Valid name: alphabetic with spaces, at least 2 words
        if re.match(r'^[A-Za-z][A-Za-z\s]+$', text) and len(text.split()) >= 2:
            result["name"] = text.title()
            return


def _extract_dob(lines, result, doc_type):
    """Extract Date of Birth. For DL, ONLY picks dates labeled as DOB/Date Of Birth."""
    
    # Strategy 1: Label on SAME line
    for line in lines:
        upper = line.upper().strip()
        m = re.search(
            r'(?:D\.?O\.?B\.?|DATE\s*OF\s*BIRTH)\s*[:：]\s*(\d{2}[-/]\d{2}[-/]\d{4})',
            upper
        )
        if m:
            result["dob"] = _format_date(m.group(1))
            return
    
    # Strategy 2: Label on one line, date on NEXT line
    for i, line in enumerate(lines):
        upper = line.upper().strip()
        if re.search(r'(?:D\.?O\.?B\.?|DATE\s*OF\s*BIRTH)\s*[:：]?\s*$', upper):
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                m = re.search(r'(\d{2}[-/]\d{2}[-/]\d{4})', next_line)
                if m:
                    result["dob"] = _format_date(m.group(1))
                    return
    
    # Strategy 3: Fallback — first date NOT on Issue/Validity line (non-DL only)
    if doc_type not in ["DL"]:
        for line in lines:
            upper = line.upper()
            if any(w in upper for w in ["ISSUE", "VALID", "EXPIR", "VID"]):
                continue
            m = re.search(r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b', upper)
            if m:
                result["dob"] = _format_date(m.group(1))
                return


def _extract_address_and_phone(lines, result, doc_type):
    """
    Extract address and phone number from ANY side of the ID.
    
    Key fix for DL: OCR may interleave right-side text (Holder's Signature,
    Organ Donor) between address lines. We SKIP those noise lines instead
    of stopping the capture.
    
    Also extracts phone from DL "MOB NO 8980801979" pattern.
    Returns a single combined address string.
    """
    address_lines = []
    capturing = False
    
    for line in lines:
        text = line.strip()
        upper = text.upper()
        
        # ---- Detect address start marker ----
        if re.search(r'\bADDRESS\b', upper) or re.search(r'\bADD\s*:', upper):
            capturing = True
            # Check if content is on the same line after the label
            after = re.split(r'(?:ADDRESS|ADD)\s*[:：]?\s*', upper, maxsplit=1)
            if len(after) > 1 and len(after[-1].strip()) > 2:
                address_lines.append(after[-1].strip().title())
            continue
        
        if capturing:
            # SKIP noise lines but DON'T stop capturing
            # DL has "Holder's Signature", "Organ Donor: No" on the right side
            # OCR may interleave these between address lines
            if re.search(r'\b(HOLDER|SIGNATURE|ORGAN\s*DONOR|BLOOD\s*GROUP)\b', upper):
                continue  # Skip this line, keep looking for more address
            
            # Actually stop only for truly unrelated content (next section)
            if re.search(r'\b(VID|DOWNLOAD|HELP|WWW\.|1947|ISSUE\s*DATE|NAME\s*:)\b', upper):
                capturing = False
                continue
            
            # Skip non-ASCII (Gujarati/Hindi duplicate)
            if any(ord(c) > 127 for c in text):
                continue
            
            # Skip extremely short noise (1-2 chars) or specific artifacts like 'Dat'
            if (len(text) <= 2 and not any(c.isdigit() for c in text)) or upper in ['DAT', 'DAT,']:
                continue
            
            address_lines.append(text.title())
            
            # Pin code (6 digits) usually marks end of address
            if re.search(r'\b\d{6}\b', text):
                capturing = False
    
    # ---- FALLBACK for DL: address-like patterns when "Address" label not found ----
    if not address_lines and doc_type == "DL":
        print("[OCR] Address label not found, trying DL address pattern fallback...")
        for i, line in enumerate(lines):
            upper = line.upper()
            # Common Indian address starters
            if re.search(r'\b(FLAT\s*N|HOUSE\s*N|ROOM\s*N|PLOT|BLOCK|BLDG|BUILDING|STREET|ROAD|LANE|NAGAR|COLONY|SECTOR|VILLAGE|DIST)\b', upper):
                # Capture from this line onward (max 5 lines)
                for j in range(i, min(i + 5, len(lines))):
                    addr_text = lines[j].strip()
                    addr_upper = addr_text.upper()
                    if re.search(r'\b(HOLDER|SIGNATURE|ORGAN|VID|DOWNLOAD)\b', addr_upper):
                        continue
                    if any(ord(c) > 127 for c in addr_text):
                        continue
                    if len(addr_text) < 3:
                        continue
                    address_lines.append(addr_text.title())
                    if re.search(r'\b\d{6}\b', addr_text):
                        break
                break
    
    # ---- Extract phone number from address lines ----
    cleaned = []
    for al in address_lines:
        # Pattern 1: "MOB NO 8980801979" or "MOBILE NUMBER 8980801979"
        m = re.search(r'MOB(?:ILE)?\s*(?:NO|NUMBER|\.?)\s*[:.]?\s*(\d{10})', al, re.IGNORECASE)
        if m:
            result["phone"] = m.group(1)
            al = re.sub(
                r',?\s*MOB(?:ILE)?\s*(?:NO|NUMBER|\.?)\s*[:.]?\s*\d{10}',
                '', al, flags=re.IGNORECASE
            ).strip()
        
        # Pattern 2: standalone 10-digit number after comma in address
        if not result["phone"]:
            m2 = re.search(r',\s*(\d{10})\b', al)
            if m2:
                result["phone"] = m2.group(1)
                al = re.sub(r',\s*\d{10}\b', '', al).strip()
        
        # Clean up trailing commas
        al = al.rstrip(',').strip()
        if al:
            cleaned.append(al)
    address_lines = cleaned
    
    # ---- Combine into single address string (as-is) ----
    if address_lines:
        result["address"] = ", ".join(address_lines)
        result["address"] = result["address"].strip().rstrip(',').strip()


def _format_date(date_str):
    """Convert DD/MM/YYYY or DD-MM-YYYY to YYYY-MM-DD for HTML date input."""
    d_str = date_str.replace("/", "-")
    parts = d_str.split("-")
    if len(parts) == 3 and len(parts[2]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return d_str

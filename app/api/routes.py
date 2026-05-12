"""
API Routes
All FastAPI endpoints for vehicle logging system
"""
from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
import uuid
import shutil

from .db_sqlite import (
    create_visit,
    close_visit,
    update_latest_visit_details_by_vehicle,
    find_open_visit_by_vehicle,
    get_all_visits,
    get_stats,
    is_regular_user,
    get_regular_user,
    mark_regular_user,
    get_all_regular_users,
    delete_regular_user,
    update_kiosk_visit_details,
    delete_visit
)
from .id_ocr import extract_id_details
from .db_sqlite import search_staff
from .email_utils import send_visitor_notification

router = APIRouter()

# Global state: tracks if a visitor is currently filling the kiosk form
KIOSK_LOCKED_VEHICLE = None

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "..", "web", "templates")
templates = Jinja2Templates(directory=templates_path)

# Pydantic models for request/response
class NewEntryRequest(BaseModel):
    vehicle_no: str
    image_path: str
    in_time: Optional[str] = None
    name: Optional[str] = ""
    phone: Optional[str] = ""
    purpose: Optional[str] = ""

class UpdateExitRequest(BaseModel):
    vehicle_no: str
    out_time: Optional[str] = None

class UpdateDetailsRequest(BaseModel):
    vehicle_no: str
    name: str
    phone: str
    purpose: str

class VehicleEntry(BaseModel):
    vehicle_no: str
    visitor_name: str
    phone: str
    purpose: str
    in_time: str
    out_time: str
    image_path: str


# API Endpoints

@router.post("/new-entry")
async def create_new_entry(entry: NewEntryRequest):
    """
    Create a new vehicle entry (IN time)
    Called by device when a new vehicle arrives
    """
    global KIOSK_LOCKED_VEHICLE
    try:
        in_time = entry.in_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Check if vehicle already has an open entry
        existing_row = find_open_visit_by_vehicle(entry.vehicle_no)
        
        if existing_row:
            return {
                "status": "warning",
                "message": f"Vehicle {entry.vehicle_no} already has an open entry",
                "existing_entry": {
                    "in_time": existing_row.get("in_time"),
                    "name": existing_row.get("visitor_name"),
                    "phone": existing_row.get("phone"),
                    "purpose": existing_row.get("purpose")
                }
            }
        
        # Check if regular user (worker) to set visitor type
        worker_info = get_regular_user(entry.vehicle_no)
        
        if worker_info:
            visitor_type = "worker"
            # Auto-fill name and phone
            entry.name = entry.name or worker_info.get("user_name", "")
            entry.phone = entry.phone or worker_info.get("phone", "")
            entry.purpose = entry.purpose or "Worker Entry"
            response_status = "worker_entry"
        else:
            visitor_type = "visitor"
            response_status = "new"
            # LOCK kiosk for this visitor
            KIOSK_LOCKED_VEHICLE = entry.vehicle_no
            print(f"[LOCK] Kiosk locked for: {KIOSK_LOCKED_VEHICLE}")
        
        # Create new entry
        create_visit(
            vehicle_no=entry.vehicle_no,
            image_path=entry.image_path,
            visitor_type=visitor_type
        )
        
        # We update the details immediately 
        if entry.name or entry.phone or entry.purpose:
            update_latest_visit_details_by_vehicle(
                entry.vehicle_no,
                entry.name,
                entry.phone,
                entry.purpose
            )
        
        return {
            "status": response_status,
            "message": f"New entry created for vehicle {entry.vehicle_no}. Type: {visitor_type}",
            "vehicle_no": entry.vehicle_no,
            "in_time": in_time,
            "visitor_type": visitor_type,
            "name": entry.name
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating entry: {str(e)}")


@router.post("/update-exit")
async def update_exit_time(exit_data: UpdateExitRequest):
    """
    Update vehicle exit time (OUT time)
    Called by device when a vehicle exits
    """
    try:
        out_time = exit_data.out_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        success = close_visit(exit_data.vehicle_no)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No open entry found for vehicle {exit_data.vehicle_no}"
            )
        
        return {
            "status": "success",
            "message": f"Exit time updated for vehicle {exit_data.vehicle_no}",
            "vehicle_no": exit_data.vehicle_no,
            "out_time": out_time
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating exit: {str(e)}")


@router.post("/update-details")
async def update_visitor_details(details: UpdateDetailsRequest):
    """
    Update visitor details (name, phone, purpose) for an existing entry
    Called from the visitor form submission
    """
    try:
        success = update_latest_visit_details_by_vehicle(
            details.vehicle_no,
            details.name,
            details.phone,
            details.purpose
        )
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No open entry found for vehicle {details.vehicle_no}"
            )
        
        return {
            "status": "success",
            "message": f"Visitor details updated for vehicle {details.vehicle_no}",
            "vehicle_no": details.vehicle_no
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating details: {str(e)}")


@router.get("/vehicles")
async def get_all_vehicles():
    """
    Get all vehicle entries from the system
    Returns list of all logged vehicles
    """
    try:
        vehicles = get_all_visits(limit=500)
        
        return {
            "status": "success",
            "count": len(vehicles),
            "vehicles": vehicles
        }
    
    except Exception as e:
        print(f"[ERROR] /api/vehicles failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching vehicles: {str(e)}")


@router.get("/stats")
async def get_statistics():
    """
    Get system statistics
    Returns counts and analytics about vehicle entries
    """
    try:
        stats = get_stats()
        
        return {
            "status": "success",
            "statistics": stats
        }
    
    except Exception as e:
        print(f"[ERROR] /api/stats failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@router.get("/vehicle/{vehicle_no}")
async def get_vehicle_by_number(vehicle_no: str):
    """
    Get all entries for a specific vehicle number
    """
    try:
        from .db_sqlite import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM visits WHERE vehicle_no = ? ORDER BY in_time DESC', (vehicle_no,))
        rows = cursor.fetchall()
        conn.close()
        
        vehicle_entries = [dict(row) for row in rows]
        
        if not vehicle_entries:
            raise HTTPException(
                status_code=404,
                detail=f"No entries found for vehicle {vehicle_no}"
            )
        
        return {
            "status": "success",
            "vehicle_no": vehicle_no,
            "count": len(vehicle_entries),
            "entries": vehicle_entries
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching vehicle: {str(e)}")

# New classification endpoints

@router.get("/check-vehicle/{vehicle_no}")
async def check_vehicle_type(vehicle_no: str):
    """
    Checks if a vehicle is a regular user or visitor
    """
    try:
        if is_regular_user(vehicle_no):
            return {"status": "success", "type": "regular"}
        return {"status": "success", "type": "visitor"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking vehicle type: {str(e)}")

class MarkRegularRequest(BaseModel):
    vehicle_no: str
    name: Optional[str] = ""
    phone: Optional[str] = ""

@router.post("/mark-regular")
async def mark_vehicle_as_regular(info: MarkRegularRequest):
    """
    Whitelists a regular vehicle in the database
    """
    try:
        success = mark_regular_user(info.vehicle_no, info.name, info.phone, "")
        if success:
            return {"status": "success", "message": f"{info.vehicle_no} marked as Regular User"}
        raise HTTPException(status_code=500, detail="Failed to mark as regular")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@router.get("/workers")
async def get_workers():
    """
    Get all regular users (workers)
    """
    try:
        workers = get_all_regular_users()
        return {
            "status": "success",
            "count": len(workers),
            "workers": workers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching workers: {str(e)}")

class AddWorkerRequest(BaseModel):
    vehicle_no: str
    name: str
    phone: str
    department: Optional[str] = ""
    id_type: Optional[str] = ""
    id_number: Optional[str] = ""
    id_card_front_path: Optional[str] = ""
    id_card_back_path: Optional[str] = ""
    dob: Optional[str] = ""
    address_street: Optional[str] = ""
    address_city: Optional[str] = ""
    address_state: Optional[str] = ""

@router.post("/add-worker")
async def add_worker(worker: AddWorkerRequest):
    """
    Add a new worker to the database
    """
    try:
        success = mark_regular_user(
            vehicle_no=worker.vehicle_no, 
            name=worker.name, 
            phone=worker.phone, 
            flat_no=worker.department,
            id_type=worker.id_type,
            id_number=worker.id_number,
            id_card_front_path=worker.id_card_front_path,
            id_card_back_path=worker.id_card_back_path,
            dob=worker.dob,
            address_street=worker.address_street,
            address_city=worker.address_city,
            address_state=worker.address_state
        )
        if success:
            return {"status": "success", "message": f"Worker {worker.name} added successfully"}
        raise HTTPException(status_code=500, detail="Failed to add worker")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding worker: {str(e)}")

@router.delete("/delete-worker/{vehicle_no}")
async def delete_worker(vehicle_no: str):
    """
    Remove a worker from the database
    """
    try:
        success = delete_regular_user(vehicle_no)
        if success:
            return {"status": "success", "message": f"Worker {vehicle_no} deleted successfully"}
        raise HTTPException(status_code=404, detail=f"Worker with plate {vehicle_no} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting worker: {str(e)}")


# Web Form Routes (served via FastAPI)

@router.get("/form", response_class=HTMLResponse)
async def visitor_form_page(request: Request, plate: str = ""):
    """
    Serve the visitor entry form
    """
    return templates.TemplateResponse(
        request,
        "form.html",
        {"plate": plate, "success_message": None}
    )


@router.post("/form", response_class=HTMLResponse)
async def submit_visitor_form(
    request: Request,
    vehicle: str = Form(...),
    name: str = Form(...),
    phone: str = Form(...),
    purpose: str = Form(...)
):
    """
    Handle visitor form submission
    """
    try:
        success = update_latest_visit_details_by_vehicle(vehicle, name, phone, purpose)
        
        success_message = "Visitor logged successfully!" if success else "Error updating details"
        
        return templates.TemplateResponse(
            request,
            "form.html",
            {
                "plate": vehicle,
                "success_message": success_message
            }
        )
    
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "form.html",
            {
                "plate": vehicle,
                "success_message": f"Error: {str(e)}"
            }
        )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Serve the dashboard page
    """
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {}
    )


# Phase 5: Kiosk Form Routes

@router.get("/kiosk", response_class=HTMLResponse)
async def kiosk_form_page(request: Request, plate: str = ""):
    """
    Serve the kiosk visitor entry form
    """
    return templates.TemplateResponse(
        request,
        "kiosk.html",
        {"plate": plate}
    )

@router.post("/kiosk")
async def submit_kiosk_form(request: Request):
    """
    Handle visitor form submission from kiosk
    Receives JSON payload with all required fields
    """
    global KIOSK_LOCKED_VEHICLE
    try:
        data = await request.json()
        vehicle_no = data.get('vehicle_no')
        
        if not vehicle_no:
            raise HTTPException(status_code=400, detail="Vehicle number is required")
            
        success = update_kiosk_visit_details(vehicle_no, data)
        
        if success:
            # UNLOCK kiosk — camera can resume
            print(f"[UNLOCK] Kiosk released for: {KIOSK_LOCKED_VEHICLE}")
            KIOSK_LOCKED_VEHICLE = None
            
            # --- Phase 7: Email Notification ---
            faculty_email = data.get('person_to_meet_email')
            faculty_name = data.get('person_to_meet')
            visitor_name = data.get('visitor_name')
            purpose = data.get('purpose')
            address = data.get('address', '-')
            
            if faculty_email and faculty_name:
                # Run in background to not block the response
                import threading
                threading.Thread(
                    target=send_visitor_notification,
                    args=(faculty_email, faculty_name, visitor_name, vehicle_no, purpose, address)
                ).start()

            return {"status": "success", "message": "Visitor details logged successfully"}
        else:
            raise HTTPException(status_code=404, detail="No open visit found for this vehicle")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing kiosk submission: {str(e)}")

@router.post("/upload-id-card")
async def upload_id_card(file: UploadFile = File(...)):
    """
    Handle ID card image uploads from the kiosk camera or file picker
    """
    try:
        from datetime import datetime
        date_str = datetime.now().strftime("%d-%m-%Y")
        
        # Base directory for uploads
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(base_dir, "data", "id_cards", date_str)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Generate unique filename
        file_ext = os.path.splitext(file.filename)[1]
        if not file_ext:
            file_ext = '.jpg'
            
        filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(upload_dir, filename)
        
        # Write file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Return relative path for saving to database
        rel_path = os.path.join("data", "id_cards", date_str, filename).replace("\\", "/")
        
        return {
            "status": "success", 
            "message": "File uploaded successfully",
            "file_path": rel_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

class IDOCRRequest(BaseModel):
    image_path: str
    side: str = "front"

@router.post("/id-ocr")
async def id_card_ocr(request: IDOCRRequest):
    """
    Extract details from an ID card image using Azure OCR
    """
    try:
        result = extract_id_details(request.image_path, request.side)
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing OCR: {str(e)}")

@router.get("/staff-search")
async def staff_search(q: str = ""):
    """Search for faculty/staff members for autocomplete."""
    try:
        results = search_staff(q)
        return {"status": "success", "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/manual-entry")
async def manual_entry():
    """Manually creates a test entry and redirects to kiosk."""
    try:
        import time
        # Generate a unique test plate
        test_plate = f"TEST_{int(time.time()) % 10000}"
        
        # Create the 'inside' record in DB
        create_visit(
            vehicle_no=test_plate,
            image_path="", # No image for manual
            visitor_type="visitor"
        )
        
        # Redirect to kiosk form for this plate
        return RedirectResponse(url=f"/api/kiosk?plate={test_plate}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual entry failed: {str(e)}")

# --- Kiosk Status & Cleanup ---

@router.get("/kiosk-status")
async def get_kiosk_status():
    """Camera runner polls this to know if form is still being filled."""
    global KIOSK_LOCKED_VEHICLE
    if KIOSK_LOCKED_VEHICLE:
        return {"status": "busy", "vehicle_no": KIOSK_LOCKED_VEHICLE}
    return {"status": "ready"}

@router.delete("/delete-visit/{visit_id}")
async def delete_visit_endpoint(visit_id: int):
    """Delete a visit entry (for cleanup from dashboard)."""
    global KIOSK_LOCKED_VEHICLE
    if delete_visit(visit_id):
        KIOSK_LOCKED_VEHICLE = None  # Also clear any lock
        return {"status": "success", "message": "Entry deleted"}
    raise HTTPException(status_code=404, detail="Visit not found")

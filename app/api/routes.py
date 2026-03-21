"""
API Routes
All FastAPI endpoints for vehicle logging system
"""
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

from .db_sqlite import (
    create_visit,
    close_visit,
    update_latest_visit_details_by_vehicle,
    find_open_visit_by_vehicle,
    get_all_visits,
    get_stats,
    is_regular_user,
    mark_regular_user
)

router = APIRouter()

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
        
        # Check if regular user to set visitor type
        visitor_type = "regular" if is_regular_user(entry.vehicle_no) else "visitor"
        
        # Create new entry
        create_visit(
            vehicle_no=entry.vehicle_no,
            image_path=entry.image_path,
            visitor_type=visitor_type
        )
        
        # We optionally update the details immediately if passed in the new entry
        if entry.name or entry.phone or entry.purpose:
            update_latest_visit_details_by_vehicle(
                entry.vehicle_no,
                entry.name,
                entry.phone,
                entry.purpose
            )
        
        return {
            "status": "success",
            "message": f"New entry created for vehicle {entry.vehicle_no}. Type: {visitor_type}",
            "vehicle_no": entry.vehicle_no,
            "in_time": in_time,
            "visitor_type": visitor_type
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
        success = mark_regular_user(info.vehicle_no, info.name, info.phone)
        if success:
            return {"status": "success", "message": f"{info.vehicle_no} marked as Regular User"}
        raise HTTPException(status_code=500, detail="Failed to mark as regular")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# Web Form Routes (served via FastAPI)

@router.get("/form", response_class=HTMLResponse)
async def visitor_form_page(request: Request, plate: str = ""):
    """
    Serve the visitor entry form
    """
    return templates.TemplateResponse(
        "form.html",
        {"request": request, "plate": plate, "success_message": None}
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
            "form.html",
            {
                "request": request,
                "plate": vehicle,
                "success_message": success_message
            }
        )
    
    except Exception as e:
        return templates.TemplateResponse(
            "form.html",
            {
                "request": request,
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
        "dashboard.html",
        {"request": request}
    )

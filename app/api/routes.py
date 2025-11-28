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

from app.api.csv_utils import (
    append_entry,
    read_all_rows,
    update_out_time,
    update_visitor_details_for_last,
    find_last_open_entry,
    get_vehicle_stats
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
        idx, existing_row = find_last_open_entry(entry.vehicle_no)
        
        if idx is not None:
            return {
                "status": "warning",
                "message": f"Vehicle {entry.vehicle_no} already has an open entry",
                "existing_entry": {
                    "in_time": existing_row[4],
                    "name": existing_row[1],
                    "phone": existing_row[2],
                    "purpose": existing_row[3]
                }
            }
        
        # Create new entry
        append_entry(
            vehicle_no=entry.vehicle_no,
            image_path=entry.image_path,
            in_time=in_time,
            name=entry.name,
            phone=entry.phone,
            purpose=entry.purpose
        )
        
        return {
            "status": "success",
            "message": f"New entry created for vehicle {entry.vehicle_no}",
            "vehicle_no": entry.vehicle_no,
            "in_time": in_time
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
        
        success = update_out_time(exit_data.vehicle_no, out_time)
        
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
        success = update_visitor_details_for_last(
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
        rows = read_all_rows()
        
        # Skip header row
        vehicles = []
        for row in rows[1:]:
            if len(row) >= 7:
                vehicles.append({
                    "vehicle_no": row[0],
                    "visitor_name": row[1],
                    "phone": row[2],
                    "purpose": row[3],
                    "in_time": row[4],
                    "out_time": row[5],
                    "image_path": row[6]
                })
        
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
        stats = get_vehicle_stats()
        
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
        rows = read_all_rows()
        
        vehicle_entries = []
        for row in rows[1:]:
            if len(row) >= 7 and row[0] == vehicle_no:
                vehicle_entries.append({
                    "vehicle_no": row[0],
                    "visitor_name": row[1],
                    "phone": row[2],
                    "purpose": row[3],
                    "in_time": row[4],
                    "out_time": row[5],
                    "image_path": row[6]
                })
        
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
        success = update_visitor_details_for_last(vehicle, name, phone, purpose)
        
        success_message = "✅ Visitor logged successfully!" if success else "❌ Error updating details"
        
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
                "success_message": f"❌ Error: {str(e)}"
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

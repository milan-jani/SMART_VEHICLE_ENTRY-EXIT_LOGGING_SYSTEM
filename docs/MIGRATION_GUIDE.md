# Migration Guide

## Overview
This document explains how the old structure was refactored into the new clean architecture.

---

## File Migrations

### Old Structure → New Structure

#### Core Application Files

| Old Path | New Path | Changes |
|----------|----------|---------|
| `app/api.py` | `app/device/camera.py` + `app/device/anpr.py` | Split camera capture and ANPR logic |
| `app/camera.py` | `app/device/camera.py` | Empty file → Populated with camera logic |
| `app/anpr.py` | `app/device/anpr.py` | Empty file → Populated with ANPR logic |
| `app/config.py` | `app/device/config.py` | Empty file → Populated with configuration |
| `app/csv_utils.py` | `app/api/csv_utils.py` | Moved to API layer (backend only) |
| `app/server.py` | `app/api/routes.py` | Flask → FastAPI, integrated into routes |
| `app/run.py` | `app/device/device_runner.py` | Refactored to use API calls instead of direct CSV |

#### New Files Created

| New File | Purpose |
|----------|---------|
| `app/main.py` | FastAPI entry point and application initialization |
| `app/api/routes.py` | All API endpoints (new-entry, update-exit, vehicles, stats, form) |
| `app/device/device_runner.py` | Device workflow that calls API endpoints |
| `app/web/templates/dashboard.html` | New dashboard for viewing all vehicles |
| `app/web/static/js/dashboard.js` | Dashboard JavaScript for data fetching |

#### Frontend Files

| Old Path | New Path | Changes |
|----------|----------|---------|
| `app/templates/form.html` | `app/web/templates/form.html` | Updated form action to use FastAPI endpoint |
| `app/static/css/style.css` | `app/web/static/css/style.css` | Same content, new location |
| N/A | `app/web/templates/dashboard.html` | NEW: Dashboard page |
| N/A | `app/web/static/js/dashboard.js` | NEW: Dashboard JavaScript |

#### Data Files

| Old Path | New Path | Changes |
|----------|----------|---------|
| `data/visitors.csv` | `data/visitors.csv` | Same location, no changes |
| `images/*.jpg` | `data/photos/*.jpg` | Images now stored in data/photos |

---

## Key Architectural Changes

### 1. **API Layer (Backend)**
- **Old**: Flask server (`server.py`) with direct CSV writes
- **New**: FastAPI backend (`main.py` + `api/routes.py`) with proper REST endpoints
- **Benefits**: 
  - RESTful API design
  - Automatic API documentation
  - Better error handling
  - Type validation with Pydantic

### 2. **Device Layer**
- **Old**: Device code directly wrote to CSV
- **New**: Device code calls API endpoints
- **Benefits**:
  - Separation of concerns
  - Can run device on different machine
  - Better error handling and logging
  - API-first design

### 3. **Web Layer**
- **Old**: Flask templates mixed with application code
- **New**: Dedicated `web/` folder with templates and static files
- **Benefits**:
  - Clear separation of frontend and backend
  - Easy to add new pages
  - Better organization

---

## Code Changes Explained

### Old `app/run.py` → New `app/device/device_runner.py`

**Before:**
```python
# Directly wrote to CSV
csv_utils.append_entry(plate_number, image_path, now_time)
csv_utils.update_out_time(plate_number, now_time)
```

**After:**
```python
# Calls API endpoints
requests.post(API_NEW_ENTRY, json=payload)
requests.post(API_UPDATE_EXIT, json=payload)
```

### Old `app/server.py` → New `app/api/routes.py`

**Before:**
```python
@app.route("/", methods=["GET", "POST"])
def visitor_form():
    # Flask route
    csv_utils.update_visitor_details_for_last(...)
```

**After:**
```python
@router.post("/form")
async def submit_visitor_form(...):
    # FastAPI route
    update_visitor_details_for_last(...)
```

### Old `app/api.py` → New Split Files

**Before:**
```python
# camera.py had everything mixed
def capture_with_preview():
    # camera code
    # ANPR API call
    # both together
```

**After:**
```python
# app/device/camera.py
def capture_with_preview():
    # only camera logic

# app/device/anpr.py
def detect_plate_from_image(image_path):
    # only ANPR logic
```

---

## New API Endpoints

The new architecture provides these REST endpoints:

### Vehicle Operations
- `POST /api/new-entry` - Create vehicle entry (replaces direct CSV write)
- `POST /api/update-exit` - Update exit time (replaces direct CSV write)
- `POST /api/update-details` - Update visitor info
- `GET /api/vehicles` - Get all vehicles
- `GET /api/vehicle/{vehicle_no}` - Get specific vehicle
- `GET /api/stats` - Get statistics

### Web Pages
- `GET /api/form?plate={number}` - Visitor entry form
- `POST /api/form` - Submit form
- `GET /api/dashboard` - Dashboard page

---

## How to Run

### Old Way
```bash
python app/run.py  # Everything in one process
```

### New Way
```bash
# Terminal 1: Start backend
python -m uvicorn app.main:app --reload

# Terminal 2: Run device
python -m app.device.device_runner
```

Or use the convenient scripts:
```bash
# Windows
start.bat          # Start backend
run_device.bat     # Run device

# Linux/Mac
./start.sh         # Start backend
./run_device.sh    # Run device
```

---

## Configuration Changes

### Old
- Hardcoded values in each file
- No centralized config

### New
- `app/device/config.py` - All device configuration
- `.env.example` - Environment variables template
- Easy to switch between development and production

---

## Benefits of New Structure

1. **Modularity**: Each component has a specific responsibility
2. **Scalability**: Can deploy backend and device separately
3. **Maintainability**: Easier to find and modify code
4. **Testability**: Components can be tested independently
5. **API-First**: Other apps can consume the same API
6. **Docker-Ready**: Proper Dockerfile and docker-compose
7. **Production-Ready**: Clean separation, proper error handling
8. **Dashboard**: New UI to view all data in real-time

---

## Migration Checklist

- [x] Backend API created with FastAPI
- [x] Device code refactored to use API
- [x] CSV operations moved to API layer only
- [x] Templates moved to web/ folder
- [x] Static files organized properly
- [x] Dashboard page created
- [x] Dockerfile created
- [x] docker-compose.yml created
- [x] README updated
- [x] Startup scripts created
- [x] .gitignore added
- [x] requirements.txt updated

---

## What to Test

1. **Backend Server**
   ```bash
   python -m uvicorn app.main:app --reload
   # Visit http://localhost:8000/docs
   ```

2. **Device Workflow**
   ```bash
   python -m app.device.device_runner
   ```

3. **Dashboard**
   - Visit http://localhost:8000/api/dashboard
   - Should show all vehicles

4. **Form**
   - Visit http://localhost:8000/api/form?plate=TEST123
   - Submit form
   - Check CSV updated

5. **API Endpoints**
   - Use http://localhost:8000/docs to test all endpoints

---

## Troubleshooting

### Import Errors
- Make sure you're running from project root
- Use `python -m app.main` not `python app/main.py`

### API Connection Failed
- Ensure backend is running first
- Check `API_BASE_URL` in `app/device/config.py`

### Camera Issues
- Update `DEFAULT_CAMERA_INDEX` in config
- Check camera permissions

---

**Your old code is preserved - just reorganized! 🎉**

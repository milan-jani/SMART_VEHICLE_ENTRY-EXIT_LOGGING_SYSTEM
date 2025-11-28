# Testing Checklist

Use this checklist to verify that your refactored system works correctly.

---

## ✅ Pre-Test Setup

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Ensure camera is connected (if testing device)
- [ ] Check PlateRecognizer API key in `app/device/config.py`
- [ ] Ensure `data/visitors.csv` exists (will be created automatically)

---

## 🧪 Test 1: Backend Server

### Start the server:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Checklist:
- [ ] Server starts without errors
- [ ] Visit http://localhost:8000
  - [ ] Shows: `{"status": "running", "message": "Hybrid Logging System API", "version": "2.0.0"}`
- [ ] Visit http://localhost:8000/docs
  - [ ] Shows interactive API documentation (Swagger UI)
  - [ ] All endpoints visible
- [ ] No error logs in terminal

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 2: Dashboard Page

### URL: http://localhost:8000/api/dashboard

### Checklist:
- [ ] Dashboard page loads
- [ ] Shows 4 statistics cards:
  - [ ] Total Entries
  - [ ] Currently Inside
  - [ ] Exited Today
  - [ ] Unique Vehicles
- [ ] Shows vehicle table with headers
- [ ] Refresh button works
- [ ] Auto-refresh works (check after 30 seconds)
- [ ] Link to form works

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 3: Visitor Form

### URL: http://localhost:8000/api/form?plate=TEST123

### Checklist:
- [ ] Form page loads
- [ ] Vehicle number field shows "TEST123"
- [ ] Vehicle number field is read-only
- [ ] Name, Phone, Purpose fields are editable
- [ ] Fill form with test data:
  - Name: "Test Visitor"
  - Phone: "1234567890"
  - Purpose: "Testing"
- [ ] Click Submit
- [ ] Success message appears
- [ ] Check `data/visitors.csv` - new entry added? ⬜ Yes / ⬜ No

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 4: API Endpoints (via Swagger UI)

### Go to: http://localhost:8000/docs

### Test POST /api/new-entry:
```json
{
  "vehicle_no": "KA01AB1234",
  "image_path": "data/photos/test.jpg",
  "in_time": "2025-11-20 10:00:00"
}
```
- [ ] Click "Try it out"
- [ ] Paste JSON
- [ ] Click "Execute"
- [ ] Response status: 200 ✅
- [ ] Message: "New entry created"

### Test GET /api/vehicles:
- [ ] Click "Try it out"
- [ ] Click "Execute"
- [ ] Response status: 200 ✅
- [ ] Returns list of vehicles
- [ ] Should include the test vehicle "KA01AB1234"

### Test GET /api/stats:
- [ ] Click "Try it out"
- [ ] Click "Execute"
- [ ] Response status: 200 ✅
- [ ] Shows correct statistics

### Test POST /api/update-exit:
```json
{
  "vehicle_no": "KA01AB1234",
  "out_time": "2025-11-20 11:00:00"
}
```
- [ ] Click "Try it out"
- [ ] Paste JSON
- [ ] Click "Execute"
- [ ] Response status: 200 ✅
- [ ] Message: "Exit time updated"

### Test GET /api/vehicle/KA01AB1234:
- [ ] Click "Try it out"
- [ ] Enter "KA01AB1234"
- [ ] Click "Execute"
- [ ] Response status: 200 ✅
- [ ] Shows entry with Out_Time filled

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 5: Device Workflow (Camera Test)

### Prerequisites:
- [ ] Backend server is running
- [ ] Camera is connected
- [ ] Good lighting

### Run device:
```bash
python -m app.device.device_runner
```

### Checklist:
- [ ] Device starts without errors
- [ ] Camera preview window opens
- [ ] Press 'c' to capture
- [ ] Image is saved to `data/photos/`
- [ ] Plate detection API is called
- [ ] Plate number is detected (or error message if no plate)
- [ ] If new vehicle:
  - [ ] API creates new entry
  - [ ] Browser opens with form
  - [ ] Form shows detected plate number
- [ ] If existing vehicle:
  - [ ] API updates exit time
  - [ ] Confirmation message shown

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 6: Device Workflow (Without Camera - Simulated)

### If you don't have a camera, test API integration:

Create a test image:
- [ ] Place any `.jpg` image in `data/photos/` folder
- [ ] Rename it to `test_plate.jpg`

Modify `device_runner.py` temporarily to skip camera:
```python
# Comment out capture_with_preview()
# Use this instead:
image_path = "data/photos/test_plate.jpg"
plate_number = "TEST456"  # Manual plate for testing
```

### Run device:
```bash
python -m app.device.device_runner
```

### Checklist:
- [ ] Device workflow executes
- [ ] API call to `/api/new-entry` succeeds
- [ ] Entry appears in CSV
- [ ] Entry appears in dashboard

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 7: Data Persistence

### Checklist:
- [ ] Stop backend server (Ctrl+C)
- [ ] Check `data/visitors.csv` exists
- [ ] Check CSV has entries from tests
- [ ] Start backend server again
- [ ] Visit dashboard
- [ ] All previous entries still visible? ⬜ Yes / ⬜ No

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 8: Error Handling

### Test invalid vehicle lookup:
- Go to: http://localhost:8000/docs
- Test GET `/api/vehicle/INVALID999`
- [ ] Response status: 404 ✅
- [ ] Error message: "No entries found"

### Test exit without entry:
- Test POST `/api/update-exit` with non-existent vehicle
```json
{
  "vehicle_no": "DOESNOTEXIST",
  "out_time": "2025-11-20 12:00:00"
}
```
- [ ] Response status: 404 ✅
- [ ] Error message: "No open entry found"

### Test device with backend stopped:
- [ ] Stop backend server
- [ ] Run device workflow
- [ ] Should show error: "API connection failed"
- [ ] Error message mentions backend not running

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 9: Docker Deployment (Optional)

### Build and run:
```bash
docker build -t hybrid-logging .
docker run -p 8000:8000 -v $(pwd)/data:/app/data hybrid-logging
```

### Checklist:
- [ ] Docker build succeeds
- [ ] Container starts
- [ ] Visit http://localhost:8000
- [ ] API is accessible
- [ ] Dashboard works
- [ ] Data persists in mounted volume

**Status:** ⬜ Pass / ⬜ Fail

---

## 🧪 Test 10: Docker Compose (Optional)

### Run:
```bash
docker-compose up -d
```

### Checklist:
- [ ] Services start successfully
- [ ] Backend is accessible
- [ ] Check logs: `docker-compose logs -f`
- [ ] Stop: `docker-compose down`

**Status:** ⬜ Pass / ⬜ Fail

---

## 📊 Overall Test Results

| Test | Status | Notes |
|------|--------|-------|
| 1. Backend Server | ⬜ | |
| 2. Dashboard Page | ⬜ | |
| 3. Visitor Form | ⬜ | |
| 4. API Endpoints | ⬜ | |
| 5. Device Workflow (Camera) | ⬜ | |
| 6. Device Workflow (Simulated) | ⬜ | |
| 7. Data Persistence | ⬜ | |
| 8. Error Handling | ⬜ | |
| 9. Docker Deployment | ⬜ | |
| 10. Docker Compose | ⬜ | |

---

## 🐛 Common Issues & Solutions

### Issue: Import errors
**Solution:** Run from project root: `python -m app.main` not `python app/main.py`

### Issue: Camera not found
**Solution:** 
- Check camera is connected
- Try different camera index in `app/device/config.py`
- Update `DEFAULT_CAMERA_INDEX` to 1 or 2

### Issue: API connection failed
**Solution:** Ensure backend is running first before starting device

### Issue: No plate detected
**Solution:**
- Check API key in `app/device/config.py`
- Ensure good lighting
- Check API credit balance at platerecognizer.com
- Try with clearer plate image

### Issue: Port 8000 already in use
**Solution:** Change port in command: `--port 8001`

### Issue: Module not found
**Solution:** Install dependencies: `pip install -r requirements.txt`

### Issue: CSV not updating
**Solution:** Check file permissions on `data/` folder

---

## ✅ Sign Off

**Tested by:** _________________

**Date:** _________________

**System Status:** ⬜ All Tests Passed ⬜ Issues Found (see notes)

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**All tests passing? Your system is production-ready! 🎉**

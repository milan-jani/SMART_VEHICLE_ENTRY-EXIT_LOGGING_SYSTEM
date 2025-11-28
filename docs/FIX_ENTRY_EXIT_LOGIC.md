# Fix Applied: Vehicle Entry/Exit Logic

## Problem
When the same vehicle number plate was detected twice, the system was opening the form again instead of marking the vehicle as exited.

## Root Cause
The device workflow was not properly handling the API response when a vehicle already had an open entry (already inside).

## Solution Applied

### File Modified: `app/device/device_runner.py`

### Changes Made:

#### 1. Updated `send_new_entry()` function
**Before:**
- Returned `True/False` (boolean)
- Didn't distinguish between new entry and existing entry

**After:**
- Returns dictionary: `{'success': bool, 'status': str}`
- Status can be: `'new'`, `'existing'`, or `'error'`
- Properly detects when API returns "warning" status (vehicle already inside)

#### 2. Updated `run_device_workflow()` logic
**Before:**
```python
if success:
    # Always opened form
    open_visitor_form()
else:
    # Always tried exit update
    send_exit_update()
```

**After:**
```python
if status == 'new':
    # New vehicle - open form
    open_visitor_form()
elif status == 'existing':
    # Already inside - mark as exit
    send_exit_update()
```

## How It Works Now

### Scenario 1: NEW Vehicle (First Time)
```
1. Capture image
2. Detect plate: "KA01AB1234"
3. API check: No open entry found
4. API creates new entry (IN time)
5. Status: "Inside"
6. ✅ Form opens for visitor details
```

### Scenario 2: EXISTING Vehicle (Second Time - Exit)
```
1. Capture image
2. Detect plate: "KA01AB1234" (same vehicle)
3. API check: Open entry found (vehicle is inside)
4. API returns "warning" status
5. Device recognizes vehicle is already inside
6. Device calls update-exit API
7. Status changed to "Exited"
8. ✅ NO form opens (just marks exit)
```

### Scenario 3: Vehicle Returns Later (Third Time - Re-entry)
```
1. Capture image
2. Detect plate: "KA01AB1234" (same vehicle again)
3. API check: Previous entry has OUT time (closed)
4. API creates NEW entry (IN time)
5. Status: "Inside"
6. ✅ Form opens again for new visit
```

## Flow Diagram

```
┌─────────────────────────────────────────┐
│  Detect Plate: "KA01AB1234"            │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│  Send to API: POST /api/new-entry       │
└───────────────┬─────────────────────────┘
                │
                ▼
        ┌───────┴────────┐
        │   API Checks    │
        │  Open Entry?    │
        └───────┬─────────┘
                │
        ┌───────┴────────┐
        │                 │
        ▼                 ▼
   ┌─────────┐      ┌──────────┐
   │   NO    │      │   YES    │
   │ (New)   │      │(Existing)│
   └────┬────┘      └─────┬────┘
        │                 │
        ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ Return:      │   │ Return:      │
│ status='new' │   │status='existing'│
└──────┬───────┘   └──────┬───────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Create Entry │   │ Update Exit  │
│ (IN time)    │   │ (OUT time)   │
│              │   │              │
│ Open Form ✅ │   │ NO Form ❌   │
└──────────────┘   └──────────────┘
```

## Testing

### Test Case 1: New Vehicle
```bash
1. Run: .\run_device.bat
2. Capture image with plate "TEST001"
3. Expected: Form opens
4. Expected Output:
   ✅ Plate detected: TEST001
   🆕 New vehicle entry created!
   📋 Vehicle TEST001 marked as INSIDE
   🌐 Opening visitor form...
```

### Test Case 2: Same Vehicle (Exit)
```bash
1. Run: .\run_device.bat again
2. Capture image with same plate "TEST001"
3. Expected: NO form, just exit recorded
4. Expected Output:
   ✅ Plate detected: TEST001
   🔄 Vehicle TEST001 is already INSIDE
   📤 Marking as EXIT...
   ✅ Vehicle TEST001 marked as EXITED!
   🚗 Exit time recorded successfully
```

### Test Case 3: Same Vehicle Returns (Re-entry)
```bash
1. Run: .\run_device.bat again
2. Capture image with same plate "TEST001"
3. Expected: Form opens (new visit)
4. Expected Output:
   ✅ Plate detected: TEST001
   🆕 New vehicle entry created!
   📋 Vehicle TEST001 marked as INSIDE
   🌐 Opening visitor form...
```

## Verification

Check the dashboard at: http://localhost:8000/api/dashboard

You should see:
- First entry: IN time set, OUT time empty, Status: "Inside"
- After second capture: OUT time filled, Status: "Exited"
- After third capture: New row with IN time, Status: "Inside"

## Files Changed
- ✅ `app/device/device_runner.py` - Logic updated

## Files NOT Changed
- `app/api/routes.py` - Already had correct logic
- `app/api/csv_utils.py` - Already had correct functions

## Status
✅ **FIXED** - Vehicle entry/exit logic now works correctly

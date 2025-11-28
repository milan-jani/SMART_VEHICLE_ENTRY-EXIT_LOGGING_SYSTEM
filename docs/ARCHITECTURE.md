# System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     HYBRID LOGGING SYSTEM ARCHITECTURE                   │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐ │
│  │   Web Browser   │      │  Device Hardware │      │  Mobile/Other    │ │
│  │                 │      │                  │      │  Applications    │ │
│  │  - Dashboard    │      │  - Camera        │      │                  │ │
│  │  - Entry Form   │      │  - Preview       │      │  - API Consumers │ │
│  └────────┬────────┘      └────────┬─────────┘      └────────┬─────────┘ │
│           │                        │                          │            │
└───────────┼────────────────────────┼──────────────────────────┼────────────┘
            │                        │                          │
            │                        │                          │
            ▼                        ▼                          ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND LAYER                               │
│                          (app/main.py + api/)                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │                        API ROUTES (routes.py)                      │    │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  POST /api/new-entry         ──┐                                   │   │
│  │  POST /api/update-exit         ├──► Vehicle Operations            │   │
│  │  POST /api/update-details      │                                   │   │
│  │  GET  /api/vehicles            │                                   │   │
│  │  GET  /api/vehicle/{no}      ──┘                                   │   │
│  │                                                                     │   │
│  │  GET  /api/stats             ──┐                                   │   │
│  │  GET  /api/dashboard           ├──► Web Pages                      │   │
│  │  GET  /api/form                │                                   │   │
│  │  POST /api/form              ──┘                                   │   │
│  │                                                                     │   │
│  └───────────────────────────┬─────────────────────────────────────────┘  │
│                               │                                             │
│                               ▼                                             │
│  ┌────────────────────────────────────────────────────────────────────┐   │
│  │                  CSV UTILITIES (csv_utils.py)                       │   │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  • append_entry()           • update_out_time()                    │   │
│  │  • read_all_rows()          • update_visitor_details_for_last()    │   │
│  │  • find_last_open_entry()   • get_vehicle_stats()                  │   │
│  │                                                                     │   │
│  └───────────────────────────┬─────────────────────────────────────────┘  │
│                               │                                             │
└───────────────────────────────┼─────────────────────────────────────────────┘
                                │
                                ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                          DATA LAYER                                         │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────┐           ┌──────────────────────────┐       │
│  │   data/visitors.csv     │           │    data/photos/          │       │
│  ├─────────────────────────┤           ├──────────────────────────┤       │
│  │ Vehicle_No              │           │  capture_1234567890.jpg  │       │
│  │ Visitor_Name            │           │  capture_1234567891.jpg  │       │
│  │ Phone                   │           │  ...                     │       │
│  │ Purpose                 │           │                          │       │
│  │ In_Time                 │           │                          │       │
│  │ Out_Time                │           │                          │       │
│  │ Image_Path              │           │                          │       │
│  └─────────────────────────┘           └──────────────────────────┘       │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘

                                ▲
                                │
                    ┌───────────┴────────────┐
                    │                        │
┌────────────────────────────────────────────────────────────────────────────┐
│                        DEVICE LOGIC LAYER                                   │
│                         (app/device/)                                       │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────┐    │
│  │              DEVICE RUNNER (device_runner.py)                      │    │
│  │                  Main Workflow Orchestrator                        │    │
│  ├────────────────────────────────────────────────────────────────────┤   │
│  │                                                                     │   │
│  │  1. Capture Image    ────────────► camera.py                       │   │
│  │  2. Detect Plate     ────────────► anpr.py                         │   │
│  │  3. Check Existing   ────────────► API Call (GET)                  │   │
│  │  4. Send New Entry   ────────────► API Call (POST /new-entry)      │   │
│  │  5. Update Exit      ────────────► API Call (POST /update-exit)    │   │
│  │  6. Open Form        ────────────► Browser                         │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────┐  ┌───────────────────┐  ┌────────────────────┐     │
│  │   camera.py      │  │     anpr.py       │  │    config.py       │     │
│  ├──────────────────┤  ├───────────────────┤  ├────────────────────┤     │
│  │ • capture_with_  │  │ • detect_plate_   │  │ • API_BASE_URL     │     │
│  │   preview()      │  │   from_image()    │  │ • Camera settings  │     │
│  │ • capture_single_│  │ • detect_plate_   │  │ • ANPR API key     │     │
│  │   frame()        │  │   with_details()  │  │ • File paths       │     │
│  └──────────────────┘  └───────────────────┘  └────────────────────┘     │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────────┐
│                       EXTERNAL SERVICES                                     │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────┐                          │
│  │    PlateRecognizer API                       │                          │
│  │    https://api.platerecognizer.com          │                          │
│  │                                              │                          │
│  │    • License Plate Detection                │                          │
│  │    • OCR Processing                         │                          │
│  │    • Confidence Scoring                     │                          │
│  └─────────────────────────────────────────────┘                          │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
                            DATA FLOW DIAGRAM
═══════════════════════════════════════════════════════════════════════════════

NEW VEHICLE ENTRY:
──────────────────

   Device              Device Layer               Backend API           Data
  ┌──────┐            ┌──────────┐              ┌──────────┐         ┌──────┐
  │Camera│────────────│  Capture │──────────────│   POST   │─────────│ CSV  │
  └──────┘   Image    │  + ANPR  │  HTTP POST   │ /new-entry│  Write  └──────┘
                      └─────┬────┘              └────┬─────┘
                            │                        │
                            │                        ▼
                            │                   ┌──────────┐
                            │                   │  Open    │
                            └───────────────────│  Form    │
                                  Browser       └──────────┘

VEHICLE EXIT:
─────────────

   Device              Device Layer               Backend API           Data
  ┌──────┐            ┌──────────┐              ┌──────────┐         ┌──────┐
  │Camera│────────────│  Capture │──────────────│   POST   │─────────│ CSV  │
  └──────┘   Image    │  + ANPR  │  HTTP POST   │/update-exit│ Update └──────┘
                      └──────────┘              └──────────┘
                                                      │
                                                      ▼
                                                 Update Out_Time


FORM SUBMISSION:
────────────────

   Browser             Backend API                   Data
  ┌────────┐          ┌──────────┐                ┌──────┐
  │ Form   │──────────│   POST   │────────────────│ CSV  │
  │Visitor │HTTP POST │  /form   │  Update Details└──────┘
  └────────┘          └──────────┘


DASHBOARD VIEW:
───────────────

   Browser             Backend API                   Data
  ┌────────┐          ┌──────────┐                ┌──────┐
  │Dashboard│─────────│   GET    │────────────────│ CSV  │
  │        │HTTP GET  │/vehicles │   Read All     └──────┘
  │        │          │  /stats  │
  └────────┘          └──────────┘


═══════════════════════════════════════════════════════════════════════════════
                      KEY ARCHITECTURAL PRINCIPLES
═══════════════════════════════════════════════════════════════════════════════

1. SEPARATION OF CONCERNS
   • Backend (API) handles ALL data operations
   • Device layer only captures and sends to API
   • Frontend consumes API for display

2. API-FIRST DESIGN
   • All operations exposed as REST endpoints
   • Device and web both use same API
   • Easy to add new clients (mobile, desktop)

3. MODULARITY
   • Each component has single responsibility
   • Easy to test and maintain
   • Can scale components independently

4. DATA INTEGRITY
   • Only API layer writes to CSV
   • Single source of truth
   • Prevents concurrent write issues

5. DOCKER-READY
   • Containerized deployment
   • Easy to scale and deploy
   • Production-ready configuration

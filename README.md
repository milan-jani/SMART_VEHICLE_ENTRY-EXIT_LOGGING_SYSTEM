# Smart Vehicle Entry-Exit Logging System

A professional, high-performance vehicle management system featuring Automatic Number Plate Recognition (ANPR), an interactive Kiosk-based visitor registration, and advanced ID Card OCR.

## Core Features

- **Automated ANPR Workflow**: Real-time vehicle detection and plate recognition.
- **Kiosk Visitor Interface**: Premium web-based form for visitor details and documentation.
- **Advanced ID OCR**: Intelligent data extraction from Indian ID cards (Aadhaar, DL, PAN) using Azure Computer Vision with spatial filtering to eliminate background noise.
- **Date-Wise Asset Management**: Automated organization of captured vehicle and ID photos into daily subfolders (DD-MM-YYYY).
- **Dual-Mode Operation**: Unified system start or independent backend/device execution.
- **Real-Time Dashboard**: Live tracking of entries, exits, and system statistics.

## Project Structure

```text
smart-vehicle-system/
├── app/
│   ├── main.py                 # Application entry point (FastAPI)
│   ├── api/                    # Backend logic & OCR services
│   │   ├── routes.py           # API endpoints & Page routing
│   │   ├── id_ocr.py           # Azure CV integration & filtering
│   │   └── database.py         # SQLite persistence layer
│   ├── device/                 # Hardware interaction layer
│   │   ├── camera.py           # Image capture logic
│   │   ├── anpr.py             # Plate recognition logic
│   │   └── device_runner.py    # Main hardware workflow
│   └── web/                    # Frontend assets
│       ├── templates/          # HTML5 Templates (Kiosk, Dashboard)
│       └── static/             # CSS3, Vanilla JS
├── data/                       # Persistent data storage
│   ├── photos/                 # Vehicle images (Organized by date)
│   ├── id_cards/               # ID scan images (Organized by date)
│   └── smart_gate.db           # SQLite database
├── scripts/                    # Maintenance & Cleanup utilities
├── archived_legacy_tests/      # Archived legacy and testing files
├── run_all.bat                 # Unified startup script
├── run_backend.bat             # Start only the API server
└── run_device.bat              # Start only the camera workflow
```

## Operational Flow

1. **Vehicle Detection**: The camera captures a high-resolution image of the vehicle.
2. **Plate Recognition**: The system extracts the plate number via ANPR.
3. **Database Check**: System checks if the vehicle is already inside.
   - **Exit**: If already inside, the system logs the exit time.
   - **Entry**: If new, it opens the Kiosk Visitor Form.
4. **Visitor Registration**: The visitor provides details on the Kiosk.
5. **ID Documentation**: Visitor scans an ID card; the system performs OCR with spatial filtering to auto-fill details (Name, DOB, Address).
6. **Logging**: All data and assets are saved and organized by date.

## Installation

1. Clone the repository and navigate to the directory.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your environment variables in `.env` (Azure CV keys, ANPR keys).

## Usage

### One-Click Start
To run the full system (Backend + Camera):
```powershell
.\run_all.bat
```

### Modular Execution
To run only the backend server:
```powershell
.\run_backend.bat
```

To run only the camera device runner:
```powershell
.\run_device.bat
```

## Asset Organization
The system automatically organizes all captured images to prevent directory clutter. Files are moved into subdirectories based on their creation date:
- `data/photos/DD-MM-YYYY/`
- `data/id_cards/DD-MM-YYYY/`

## Configuration
All system constants including camera indices, API endpoints, and filtering thresholds can be adjusted in `app/device/config.py`.

## Author
Milan Jani

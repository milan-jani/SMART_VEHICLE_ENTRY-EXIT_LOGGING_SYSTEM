# Smart Vehicle Entry-Exit Logging System

A professional, high-performance vehicle management system featuring Automatic Number Plate Recognition (ANPR), an interactive Kiosk-based visitor registration, advanced ID Card OCR, and automated faculty notifications.

## 🚀 Key Features

- **Automated ANPR Workflow**: Real-time vehicle detection and plate recognition for seamless entry/exit.
- **Kiosk Visitor Interface**: Premium web-based interface with a bottom-docked **Hybrid Virtual Keyboard** (QWERTY/Numpad) for touch-screen compatibility.
- **Advanced ID OCR**: Intelligent data extraction from Indian ID cards (Aadhaar, DL, PAN) using Azure Computer Vision with spatial noise filtering.
- **Staff Directory & Autocomplete**: Integrated faculty database with real-time suggestions. Typing a name auto-fills their **Department** and **Room/Office Number**.
- **Faculty Notifications**: Automated email notifications sent to staff members upon visitor arrival, including visitor details, purpose, and arrival time.
- **Manual Entry Support**: Start a manual visitor registration workflow directly from the dashboard for vehicles without detectable plates.
- **Date-Wise Asset Management**: Automated organization of captured vehicle and ID photos into daily subfolders (`DD-MM-YYYY`).
- **Real-Time Dashboard**: Live tracking of current visitors, historical logs, and system statistics with high-detail modal views.

## 📁 Project Structure

```text
smart-vehicle-system/
├── app/
│   ├── main.py                 # Application entry point (FastAPI)
│   ├── api/                    # Backend logic & Services
│   │   ├── routes.py           # API endpoints & Page routing
│   │   ├── id_ocr.py           # Azure CV integration & filtering
│   │   ├── db_sqlite.py        # SQLite persistence layer (Visits & Staff)
│   │   └── email_utils.py      # SMTP-based notification service
│   ├── device/                 # Hardware interaction layer
│   │   ├── camera.py           # Image capture logic
│   │   ├── anpr.py             # Plate recognition logic
│   │   └── device_runner.py    # Main hardware workflow
│   └── web/                    # Frontend assets
│       ├── templates/          # HTML5 Templates (Kiosk, Dashboard)
│       └── static/             # CSS3, Vanilla JS
├── data/                       # Persistent data storage
│   ├── captures/               # Vehicle snapshots
│   ├── id_cards/               # ID scan images
│   └── smart_gate.db           # SQLite database
├── run_all.bat                 # Unified startup script
├── run_backend.bat             # Start only the API server
└── run_device.bat              # Start only the camera workflow
```

## 🛠 Operational Flow

1. **Detection**: Camera captures vehicle snapshot; ANPR extracts plate number.
2. **Auto-Route**: System checks status:
   - **Exiting**: Logs exit time and frees the gate.
   - **Entering**: Opens Kiosk Form on the touchscreen.
3. **Registration**: 
   - Visitor fills details using the **Virtual Keyboard**.
   - **Staff Autocomplete**: Visitor selects "Person to Meet" from suggestions; Room No is auto-filled.
4. **Verification**: Visitor scans ID card; system auto-fills Name, DOB, and Address via OCR.
5. **Notification**: Upon submission, an **Email Notification** is instantly sent to the selected faculty member.
6. **Logging**: All data is synchronized and visible on the Admin Dashboard.

## ⚙ Installation & Setup

1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. **Environment Configuration**: Create a `.env` file based on `.env.example` and add:
   - `SMTP_USER` & `SMTP_PASS`: For email notifications.
   - `AZURE_CV_KEY`: For ID card OCR.
   - `PLATE_RECOGNIZER_API_KEY`: For ANPR.

## 🚀 Usage

- **Full System**: Run `.\run_all.bat`
- **Dashboard**: Access via `http://localhost:8000`
- **Manual Entry**: Click "New Entry Form" at the bottom of the Dashboard.

---
**Author**: Milan Jani

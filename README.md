# 🚗 Hybrid Logging System

A professional vehicle logging system with Automatic Number Plate Recognition (ANPR), visitor management, and real-time dashboard.

## 🏗️ Architecture

This project follows a clean, modular architecture:

```
hybrid-logging/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── api/                       # Backend API layer
│   │   ├── routes.py              # All API endpoints
│   │   └── csv_utils.py           # Data persistence
│   ├── device/                    # Device logic layer
│   │   ├── camera.py              # Camera capture
│   │   ├── anpr.py                # Plate recognition
│   │   ├── config.py              # Configuration
│   │   └── device_runner.py      # Main device workflow
│   └── web/                       # Frontend layer
│       ├── templates/             # HTML templates
│       │   ├── form.html          # Visitor entry form
│       │   └── dashboard.html     # Vehicle dashboard
│       └── static/                # CSS, JS, images
│           ├── css/style.css
│           └── js/dashboard.js
├── bin/                           # Startup scripts
│   ├── start.bat                  # Start backend (Windows)
│   ├── start.sh                   # Start backend (Linux/Mac)
│   ├── run_device.bat             # Run device (Windows)
│   └── run_device.sh              # Run device (Linux/Mac)
├── run_all.bat / .sh              # 🚀 One-click start (both services)
├── dev_mode.bat / .sh             # 🔧 Development mode (backend only)
├── data/
│   ├── visitors.csv               # Vehicle logs
│   └── photos/                    # Captured images
├── docker/                        # Docker deployment
│   ├── Dockerfile                 # Docker image
│   └── docker-compose.yml         # Docker compose
├── docs/                          # Documentation
│   ├── README.md                  # Documentation index
│   ├── ARCHITECTURE.md            # System design
│   ├── MIGRATION_GUIDE.md         # Upgrade guide
│   ├── TESTING_CHECKLIST.md       # Testing guide
│   └── ...more guides
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🎯 Features

- **ANPR Integration**: Automatic number plate recognition using PlateRecognizer API
- **Vehicle Entry/Exit Tracking**: Log in-time and out-time for all vehicles
- **Visitor Management**: Capture visitor details via web form
- **Real-time Dashboard**: View all vehicle entries and statistics
- **RESTful API**: Clean API endpoints for all operations
- **Docker Ready**: Containerized deployment support
- **Modular Design**: Separation of concerns (API, Device, Web)

## 🚀 Quick Start

### Option 1: One-Click Start (Recommended) ⚡

Start both backend and device workflow with a single command:

**Windows:**
```powershell
.\run_all.bat
```

**Linux/Mac:**
```bash
./run_all.sh
```

This will:
- ✅ Check and install dependencies
- ✅ Start the backend server
- ✅ Start the device workflow
- ✅ Open the dashboard in your browser
- ✅ Everything ready to use!

### Option 2: Development Mode (For Dashboard/Code Changes) 🔧

**Perfect for making changes to dashboard, UI, or API!**

**Windows:**
```powershell
.\dev_mode.bat
```

**Linux/Mac:**
```bash
./dev_mode.sh
```

This mode:
- ✅ Starts **only the backend** (no camera needed)
- ✅ **Auto-reload** on file changes
- ✅ Works with existing data in `data/visitors.csv`
- ✅ Just **refresh browser** to see changes instantly!
- ✅ Perfect for UI/dashboard development

**How to use:**
1. Run `dev_mode.bat` (Windows) or `./dev_mode.sh` (Linux/Mac)
2. Dashboard opens automatically at http://localhost:8000/api/dashboard
3. Make changes to HTML, CSS, JavaScript, or Python code
4. Save your file - server auto-reloads!
5. Just refresh your browser to see the changes

### Option 3: Manual Start (Advanced)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server

**Windows:**
```powershell
.\bin\start.bat
```

**Linux/Mac:**
```bash
./bin/start.sh
```

Or manually:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 3. Run the Device Workflow

In a separate terminal:

**Windows:**
```powershell
.\bin\run_device.bat
```

**Linux/Mac:**
```bash
./bin/run_device.sh
```

Or manually:
```bash
python -m app.device.device_runner
```

This will:
1. Open camera preview
2. Capture image when you press 'c'
3. Detect plate number via ANPR
4. Send data to backend API
5. Open visitor form in browser (for new entries)

### 4. Access the Dashboard

Open your browser and visit:
- **Dashboard**: http://localhost:8000/api/dashboard
- **Entry Form**: http://localhost:8000/api/form
- **API Docs**: http://localhost:8000/docs

## 📡 API Endpoints

### Vehicle Operations

- `POST /api/new-entry` - Create new vehicle entry (IN time)
- `POST /api/update-exit` - Update vehicle exit time (OUT time)
- `POST /api/update-details` - Update visitor details
- `GET /api/vehicles` - Get all vehicle entries
- `GET /api/vehicle/{vehicle_no}` - Get specific vehicle entries
- `GET /api/stats` - Get system statistics

### Web Pages

- `GET /api/form` - Visitor entry form
- `POST /api/form` - Submit visitor details
- `GET /api/dashboard` - Vehicle dashboard

## 🐳 Docker Deployment

### Build the Image

```bash
docker build -t hybrid-logging-system .
```

### Run the Container

```bash
docker run -p 8000:8000 -v $(pwd)/data:/app/data hybrid-logging-system
```

## ⚙️ Configuration

Edit `app/device/config.py` to customize:

- Camera settings
- API endpoints
- File paths
- Auto-form behavior
- PlateRecognizer API key

## 📊 Data Storage

All data is stored in `data/visitors.csv` with the following structure:

| Column | Description |
|--------|-------------|
| Vehicle_No | Vehicle number plate |
| Visitor_Name | Visitor's name |
| Phone | Contact number |
| Purpose | Purpose of visit |
| In_Time | Entry timestamp |
| Out_Time | Exit timestamp |
| Image_Path | Path to captured photo |

## 🔧 Development

### Project Structure

- **`app/api/`**: Backend API layer (FastAPI routes and data operations)
- **`app/device/`**: Device logic (camera, ANPR, workflow)
- **`app/web/`**: Frontend (HTML templates, CSS, JavaScript)
- **`data/`**: Persistent storage (CSV and images)

### Adding New Features

1. **New API Endpoint**: Add to `app/api/routes.py`
2. **Device Logic**: Modify `app/device/device_runner.py`
3. **UI Changes**: Edit templates in `app/web/templates/`
4. **Styling**: Update `app/web/static/css/style.css`

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.11+
- **Computer Vision**: OpenCV
- **ANPR**: PlateRecognizer API
- **Frontend**: HTML, CSS, JavaScript
- **Data**: CSV (easily replaceable with database)
- **Deployment**: Docker, Uvicorn

## 📝 Workflow

### New Vehicle Entry

1. Device captures image and detects plate
2. API creates new entry with IN time
3. Visitor form opens in browser
4. User fills out visitor details
5. Details are saved via API

### Vehicle Exit

1. Device captures image and detects plate
2. API checks for existing open entry
3. If found, updates OUT time
4. Entry is marked as completed

## 🔐 Security Notes

- Replace the PlateRecognizer API key in `app/device/config.py`
- Use environment variables for sensitive data in production
- Add authentication for API endpoints if needed
- Implement HTTPS in production deployment

## � Documentation

For detailed guides, see the **[docs/](docs/)** directory:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and patterns
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - Upgrade from old version
- **[Testing Checklist](docs/TESTING_CHECKLIST.md)** - Complete testing guide
- **[Refactoring Summary](docs/REFACTORING_SUMMARY.md)** - What changed
- **[Dashboard Refresh Guide](docs/DASHBOARD_REFRESH_GUIDE.md)** - Configure refresh rate
- **[Continuous Monitoring](docs/CONTINUOUS_MONITORING.md)** - Camera setup guide

📖 **[View All Documentation →](docs/README.md)**

---

## �📄 License

This project is for educational and commercial use.

## 👤 Author

Milan Jani

---

## 🆘 Troubleshooting

### Camera not found
- Check camera index in `app/device/config.py`
- Ensure camera drivers are installed
- Try different camera indices (0, 1, 2)

### API connection failed
- Ensure backend server is running
- Check API_BASE_URL in `app/device/config.py`
- Verify firewall settings

### No plate detected
- Ensure good lighting conditions
- Check image quality
- Verify PlateRecognizer API key
- Check API credit balance

---

**Happy Logging! 🚗📊**

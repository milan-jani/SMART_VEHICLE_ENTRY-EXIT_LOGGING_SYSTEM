"""
FastAPI Main Entry Point
Initializes the FastAPI application and includes all API routes
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.api.routes import router as api_router
import os

# Initialize FastAPI app
app = FastAPI(
    title="Hybrid Logging System API",
    description="Vehicle logging system with ANPR and visitor management",
    version="2.0.0"
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "web", "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "web", "templates")
templates = Jinja2Templates(directory=templates_path)

# Include API router
app.include_router(api_router, prefix="/api", tags=["API"])

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "status": "running",
        "message": "Hybrid Logging System API",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

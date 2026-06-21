import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database.connection import engine, Base, SessionLocal
from app.database.seed import seed_data
from app.routes import dashboard, profile, jobs, learning, interviews

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("expose-autospy")

# Create database tables if they do not exist
try:
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    
    # Seed mock data in case table records are empty
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
except Exception as e:
    logger.error(f"Error during startup database operations: {e}")

# Initialize FastAPI App
app = FastAPI(
    title="Expose Autospy Career OS",
    description="Production-quality lightweight MVP for software engineers to track career development.",
    version="1.0.0"
)

# Mount Static Files (style.css, main.js)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Register Routes
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(profile.router, tags=["Profile"])
app.include_router(jobs.router, tags=["Job Tracker"])
app.include_router(learning.router, tags=["Learning Tracker"])
app.include_router(interviews.router, tags=["Interview Prep"])

@app.get("/health", tags=["Health Check"])
def health_check():
    """Health check endpoint to verify web service status."""
    return {"status": "healthy", "service": "expose-autospy"}

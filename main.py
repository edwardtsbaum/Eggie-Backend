from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from endpoints import auth, activities, protocols, medications
from database.mongo import database
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Secure User System API",
    description="A privacy-focused user authentication system",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://192.168.12.214:19000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth.router)

# Include protocol routes
app.include_router(protocols.router)

# Include medication routes
app.include_router(medications.router)

# Include activity routes
app.include_router(activities.router)


@app.get("/")
async def root():
    """Root endpoint with privacy notice."""
    return {
        "message": "Secure User System API",
        "version": "1.0.0",
        "privacy": "This system is designed with user privacy as the utmost priority"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test database connection
        await database.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

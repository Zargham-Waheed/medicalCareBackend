import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.database import engine, Base
from app.auth.routes import router as auth_router

app = FastAPI(
    title="MedicalCare Backend API",
    description="Auth, OTP verification, password reset, etc.",
    version="1.0.0"
)

# CORS: allow our external frontend (VPS dashboard/iframe) to call this API
allowed_origins = [
    settings.FRONTEND_URL,
    settings.FRONTEND_URL_8081,
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include auth routes under /auth
app.include_router(auth_router, prefix="/auth", tags=["Auth"])

@app.on_event("startup")
def startup_event():
    """Auto-create tables if they don't exist.
    This lets us bootstrap the database in Cloud SQL on first deploy.
    """
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Authentication API is running"}

@app.get("/healthz")
def healthz():
    """Health check endpoint for Cloud Run uptime monitoring."""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
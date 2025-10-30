import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.auth import routes as auth_routes

app = FastAPI(
    title="MedicalCare Backend API",
    description="Auth, OTP verification, password reset, etc.",
    version="1.0.0",
)

# CORS to allow external frontend(s)
allowed_origins = [
    os.getenv("FRONTEND_URL", "*"),
    os.getenv("FRONTEND_URL_8081", "*"),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes under /auth
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])

@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "API running successfully"}


@app.on_event("startup")
def on_startup() -> None:
    # Initialize tables on startup, but don't crash service if DB is unavailable
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:
        # Log and continue so health checks still pass
        print(f"Startup DB init skipped: {exc}")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
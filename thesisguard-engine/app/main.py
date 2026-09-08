from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.services.db_service import init_schema
from app.routes import check_routes, auth_routes

import os
from dotenv import load_dotenv

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    load_dotenv()
    if not os.getenv("HF_TOKEN"):
        print("WARNING: HF_TOKEN is not set in the environment. You may experience rate limits or warnings from Hugging Face.")
    
    print("Initializing database schema...")
    init_schema()
    yield
    # Shutdown logic
    print("Shutting down...")

app = FastAPI(title="ThesisGuard Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth routes under /api/auth only
app.include_router(auth_routes.router, prefix="/api/auth", tags=["auth"])

# Register check/report routes under /api only
app.include_router(check_routes.router, prefix="/api")


@app.get("/")
def read_root():
    return {"message": "Welcome to ThesisGuard Engine API!"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

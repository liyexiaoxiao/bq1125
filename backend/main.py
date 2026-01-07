from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import init_db
from routes.auth_routes import router as auth_router
from routes.users import router as users_router
from routes.config_api import router as config_router
from routes.process import router as process_router
from routes.logs import router as logs_router
from routes.charts import router as charts_router

# Initialize FastAPI app
app = FastAPI(
    title="Fuzz Test System API",
    description="北汽模糊测试系统后端 API",
    version="1.0.0"
)

# CORS middleware - allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(config_router)
app.include_router(process_router)
app.include_router(logs_router)
app.include_router(charts_router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
async def root():
    return {"message": "Fuzz Test System API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

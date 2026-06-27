from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, CORS_ORIGINS
from routes import ai_routes, auth_routes, employee_routes, leave_routes

import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(employee_routes.router)
app.include_router(leave_routes.router)
app.include_router(ai_routes.router)

@app.get("/")
def home():
    return {"message": "LeaveIQ API is running"}


@app.on_event("startup")
def startup_event():
    port = os.environ.get("PORT", "10000")
    logger.info(f"LeaveIQ API starting on port {port}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

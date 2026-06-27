from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from config import APP_NAME, CORS_ORIGINS
from routes import ai_routes, auth_routes, employee_routes, leave_routes

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




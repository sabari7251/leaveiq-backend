import datetime
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    name:str
    email:str
    password:str

class LoginRequest(BaseModel):
    email:str
    password:str

class DBModel(BaseModel):
    id:int
    email:str
    name:str
    department:str
    role:str
    leave_balance:int
    createdAt:datetime.datetime
    
class ChatBot(BaseModel):
    question:str

class EmployeeRequest(BaseModel):
    email:str
    name:str
    department:str
    role:str
    leave_balance:int
    password:str


class LeaveRequest(BaseModel):
    id: int
    employee_id: int
    leave_type: str
    from_date: datetime.date
    to_date: datetime.date
    total_days: int
    reason: str
    status: str
    manager_comments: str
    created_at: datetime.datetime
    updated_at: datetime.datetime

class LeaveRequestResponse(BaseModel):
    employee_id: int
    leave_type: str
    from_date: datetime.date
    to_date: datetime.date
    reason: str

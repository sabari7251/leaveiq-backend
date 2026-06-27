from fastapi import APIRouter, Depends, HTTPException
import mysql.connector

from auth import create_accessToken, pwd_context
from database import get_db_cursor
from models import LoginRequest

router = APIRouter()

'''
@router.post("/register")
def register(user:RegisterRequest):
    insert_query = "Insert into users(name,email,password) values(%s,%s,%s);"
    password = pwd_context.hash(user.password)
    values=(user.name,user.email,password)
    
    try:
        cursor.execute(insert_query,values)
        mydb.commit()
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")
        
'''

@router.post("/login")
def login(user:LoginRequest, cursor=Depends(get_db_cursor)):
    select_query = "select * from employee where email=%s;"
    cursor.execute(select_query,(user.email,))
    userdata = cursor.fetchone()

    if userdata is None:
        raise HTTPException(status_code=400, detail="Email Id Not Exist")
    
    valid = pwd_context.verify(user.password,userdata["password"])
    if not valid:
        raise HTTPException(status_code=400, detail=f"Invalid Credentials")
    
    token = create_accessToken({
        "sub":userdata["email"],
        "id":userdata["id"],
        "role":userdata["role"]
    })
    
    return {
        "access_token":token,
        "token_type":"bearer"
    }

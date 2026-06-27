from fastapi import APIRouter, Depends, HTTPException, status
import mysql.connector

from auth import get_current_user, pwd_context
from database import get_db_cursor
from models import EmployeeRequest

router = APIRouter()

@router.post("/employee",status_code=status.HTTP_201_CREATED)
def insert_employee(employee:EmployeeRequest, cursor=Depends(get_db_cursor)):

    insert_query = """
        insert into employee(name,email,password,department,role,leave_balance) values(%s,%s,%s,%s,%s,%s);
    """

    password = pwd_context.hash(employee.password)

    values = (employee.name,employee.email,password,employee.department,employee.role,employee.leave_balance)

    try:
        cursor.execute(insert_query,values)
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")
    
    return {"message": "User inserted successfully"}



@router.get("/employees",status_code=status.HTTP_200_OK)
def get_all_employees(cursor=Depends(get_db_cursor), current_user=Depends(get_current_user)):
    select_query = "select * from employee;"
    cursor.execute(select_query)
    results=cursor.fetchall()
    return results

@router.get("/employees/{employee_id}",status_code=status.HTTP_200_OK)
def get_user_by_id(employee_id:int, cursor=Depends(get_db_cursor), current_user=Depends(get_current_user)):
    select_query = "select * from employee where id=%s;"
    cursor.execute(select_query,(employee_id,))
    results=cursor.fetchone()
    return results


@router.get("/employees/{id}/leave-balance",status_code=status.HTTP_200_OK)
def get_leave_balance_route(id:int, cursor=Depends(get_db_cursor), current_user=Depends(get_current_user)):
    select_query = "select * from employee where id=%s;"
    cursor.execute(select_query,(id,))
    results = cursor.fetchone()
    if results is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    response={"employee_id":results["id"],"name":results["name"],"leave_balance":results["leave_balance"]}
    return response

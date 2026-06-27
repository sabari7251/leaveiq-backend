from datetime import datetime
import os

from fastapi import BackgroundTasks, Depends, HTTPException
import mysql

from email_service import send_leave_applied_email
from database import get_db_cursor

def apply_leave(
    employee_id: int,
    leave_type: str,
    from_date: str,
    to_date: str,
    reason: str,
    cursor,
    background_tasks:BackgroundTasks,
    **kwargs
):
    insert_query = """
        insert into leave_requests(employee_id,leave_type,from_date,to_date,total_days,reason) values(%s,%s,%s,%s,%s,%s);
    """
    if isinstance(from_date, str):
        from_date = datetime.strptime(
            from_date,
            "%Y-%m-%d"
    ).date()

    if isinstance(to_date, str):
        to_date = datetime.strptime(
            to_date,
            "%Y-%m-%d"
    ).date()

    delta = to_date - from_date

    
    values=(employee_id,leave_type,from_date,to_date,delta.days,reason)

    try:
        cursor.execute(insert_query,values)
        
        cursor.execute("SELECT name, email FROM employee WHERE id = %s", (employee_id,))
        employee = cursor.fetchone()

        # send email to manager (fire and forget — don't block the response)
        background_tasks.add_task(
            send_leave_applied_email,
            os.getenv("MANAGER_EMAIL"),
            employee["name"],
            leave_type,
            str(from_date),
            str(to_date),
            delta.days,
            reason
        )
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")
    
    return {"message": "User inserted successfully"}

def get_user_by_id(employee_id:int, cursor=Depends(get_db_cursor),**kwargs):
    select_query = "select * from employee where id=%s;"
    cursor.execute(select_query,(employee_id,))
    results=cursor.fetchone()
    return results
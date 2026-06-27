import datetime
from fastapi import APIRouter, Depends, HTTPException, status
import mysql.connector

from ai import get_ai_recommendation
from auth import get_current_user
from email_service import send_leave_decision_email
from database import get_db_cursor
from models import LeaveRequestResponse

from email_service import send_leave_applied_email
import os
import asyncio
from fastapi import BackgroundTasks

router = APIRouter()

@router.post("/leave-requests",status_code=status.HTTP_201_CREATED)
def insert_leave_request(leave:LeaveRequestResponse,
        background_tasks: BackgroundTasks,
        cursor=Depends(get_db_cursor),
        current_user=Depends(
        get_current_user
    )):

    insert_query = """
        insert into leave_requests(employee_id,leave_type,from_date,to_date,total_days,reason) values(%s,%s,%s,%s,%s,%s);
    """
    delta = leave.to_date - leave.from_date

    employee_id = current_user["id"]
    values=(employee_id,leave.leave_type,leave.from_date,leave.to_date,delta.days,leave.reason)

    try:
        cursor.execute(insert_query,values)
        
        cursor.execute("SELECT name, email FROM employee WHERE id = %s", (employee_id,))
        employee = cursor.fetchone()

        # send email to manager (fire and forget — don't block the response)
        background_tasks.add_task(
            send_leave_applied_email,
            os.getenv("MANAGER_EMAIL"),
            employee["name"],
            leave.leave_type,
            str(leave.from_date),
            str(leave.to_date),
            delta.days,
            leave.reason
        )
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")
    
    return {"message": "User inserted successfully"}



@router.get("/leave-requests")
def get_leave_requests(
    status:str|None=None,
    employee_id:int|None=None,
    from_date:datetime.date|None=None,
    to_date:datetime.date|None=None,
    cursor=Depends(get_db_cursor),
    current_user=Depends(
        get_current_user
    )
    
):
    if status is not None:
        select_query = "select * from leave_requests where status=%s;"
        cursor.execute(select_query,(status,))
    elif employee_id is not None:
        select_query = "select * from leave_requests where employee_id=%s;"
        cursor.execute(select_query,(employee_id,))
    elif from_date is not None and to_date is not None:
        select_query = "select * from leave_requests where from_date=%s and to_date=%s;"
        cursor.execute(select_query,(from_date,to_date))
    else:
        select_query = "select * from leave_requests;"
        cursor.execute(select_query)
    results = cursor.fetchall()
    return results


@router.put("/leave-requests/{id}/accept",status_code=status.HTTP_200_OK)
def accept_requests(id:int,background_tasks: BackgroundTasks,
        cursor=Depends(get_db_cursor),
        current_user=Depends(
        get_current_user,
    )):

    if current_user["role"]!="Manager":
        raise HTTPException(status_code=401, detail="Only Manager has this Access")
    
    
    select_query = "select * from leave_requests where id=%s;"
    cursor.execute(select_query,(id,))
    request_data=cursor.fetchone()

    if request_data is None:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if(request_data["status"]!="Pending"):
        raise HTTPException(status_code=404, detail="Only Pending Leave Request can be Approved")
    
    join_query = "select leave_balance from employee where id=%s ;"
    cursor.execute(join_query,(request_data["employee_id"],))
    balance=cursor.fetchone()
    balance=balance["leave_balance"]

    if(balance < int(request_data["total_days"])):
        raise HTTPException(status_code=404, detail="Not Enough Leave Balance")

    try:
        accept_query="update leave_requests set status='ACCEPTED',manager_comments=%s where id=%s;"
        cursor.execute(accept_query,("Approved",id))
        reduce_query="update employee set leave_balance=leave_balance - %s where id=%s;"
        cursor.execute(reduce_query,(request_data["total_days"],request_data["employee_id"]))
        
        cursor.execute("""
        SELECT e.name, e.email, lr.leave_type, lr.from_date, lr.to_date, lr.total_days
        FROM leave_requests lr
        JOIN employee e ON lr.employee_id = e.id
        WHERE lr.id = %s
            """, (id,))
        req = cursor.fetchone()

        background_tasks.add_task(
            send_leave_decision_email,
                employee_email=req["email"],
                employee_name=req["name"],
                status="ACCEPTED",
                leave_type=req["leave_type"],
                from_date=str(req["from_date"]),
                to_date=str(req["to_date"]),
                days=req["total_days"],
                comments=""
        )
        return {"manager_comments":"Accepted"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")
    
    
@router.get("/leave-requests/{id}/recommend",status_code=status.HTTP_200_OK)
def recommend_requests(id:int, cursor=Depends(get_db_cursor), current_user=Depends(
        get_current_user
    )):

    
    select_query = "select * from leave_requests where id=%s;"
    cursor.execute(select_query,(id,))
    request_data=cursor.fetchone()

    if request_data is None:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    join_query = "select leave_balance from employee where id=%s ;"
    cursor.execute(join_query,(request_data["employee_id"],))
    balance=cursor.fetchone()
    balance=balance["leave_balance"]

    response = get_ai_recommendation(request_data["total_days"],balance,request_data["reason"])
    
    return {"recommendation": response}
    
@router.put("/leave-requests/{id}/reject",status_code=status.HTTP_200_OK)
def reject_requests(id:int,background_tasks: BackgroundTasks, cursor=Depends(get_db_cursor), current_user=Depends(
        get_current_user
    )):
    if current_user["role"]!="Manager":
        raise HTTPException(status_code=401, detail="Only Manager has this Access")
    
    select_query = "select * from leave_requests where id=%s;"
    cursor.execute(select_query,(id,))
    request_data=cursor.fetchone()

    if request_data is None:
        raise HTTPException(status_code=404, detail="Leave request not found")

    if(request_data["status"]!="Pending"):
        raise HTTPException(status_code=404, detail="Only Pending Leave Request can be Rejcted")
    

    try:
        accept_query="update leave_requests set status='Rejected',manager_comments=%s where id=%s;"
        cursor.execute(accept_query,("Rejected",id))
        
        cursor.execute("""
        SELECT e.name, e.email, lr.leave_type, lr.from_date, lr.to_date, lr.total_days
        FROM leave_requests lr
        JOIN employee e ON lr.employee_id = e.id
        WHERE lr.id = %s
            """, (id,))
        req = cursor.fetchone()

        background_tasks.add_task(
            send_leave_decision_email,
                employee_email=req["email"],
                employee_name=req["name"],
                status="REJECTED",
                leave_type=req["leave_type"],
                from_date=str(req["from_date"]),
                to_date=str(req["to_date"]),
                days=req["total_days"],
                comments=""
        )
        
        return {"manager_comments":"Reejcted"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")


@router.put("/leave-requests/{id}/cancel", status_code=status.HTTP_200_OK)
def cancel_leave_request(id: int, background_tasks: BackgroundTasks,
                         cursor=Depends(get_db_cursor),
                         current_user=Depends(get_current_user)):
    
    select_query = "select * from leave_requests where id=%s;"
    cursor.execute(select_query, (id,))
    request_data = cursor.fetchone()

    if request_data is None:
        raise HTTPException(status_code=404, detail="Leave request not found")

    # Only the employee who created the request can cancel it
    if request_data["employee_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this leave request")

    current_status = request_data["status"]
    status_upper = current_status.upper() if current_status else ""
    if status_upper not in ["PENDING", "ACCEPTED"]:
        raise HTTPException(status_code=400, detail="Only Pending or Approved leave requests can be cancelled")

    try:
        # If already accepted/approved, refund the employee's leave balance
        if status_upper == "ACCEPTED":
            refund_query = "update employee set leave_balance = leave_balance + %s where id = %s;"
            cursor.execute(refund_query, (request_data["total_days"], request_data["employee_id"]))

        # Update status to 'Cancelled'
        update_query = "update leave_requests set status = 'Cancelled' where id = %s;"
        cursor.execute(update_query, (id,))

        cursor.execute("SELECT name FROM employee WHERE id = %s", (request_data["employee_id"],))
        employee = cursor.fetchone()
        employee_name = employee["name"] if employee else "Employee"

        from email_service import send_leave_cancelled_email
        background_tasks.add_task(
            send_leave_cancelled_email,
            os.getenv("MANAGER_EMAIL"),
            employee_name,
            request_data["leave_type"],
            str(request_data["from_date"]),
            str(request_data["to_date"]),
            request_data["total_days"]
        )

        return {"message": "Leave request cancelled successfully"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=400, detail=f"Error: {err}")


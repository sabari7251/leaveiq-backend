import os

from fastapi_mail import FastMail,MessageSchema,ConnectionConfig

from ai import get_ai_apply_email
from ai import get_ai_decision_email

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
)

fm = FastMail(conf)


async def send_leave_applied_email(manager_email: str, employee_name: str, leave_type: str, from_date: str, to_date: str, days: int, reason: str):
    
    html = get_ai_apply_email(manager_email,employee_name,leave_type,from_date,to_date,days,reason)
    message = MessageSchema(
        subject=f"Leave Request from {employee_name} - {leave_type} ({days} days)",
        recipients=[manager_email],
        body=html,
        subtype="html"
    )
    await fm.send_message(message)
    
async def send_leave_decision_email(employee_email: str, employee_name: str, status: str, leave_type: str, from_date: str, to_date: str, days: int, comments: str = ""):
    
    html = get_ai_decision_email(employee_email,employee_name,status,leave_type,from_date,to_date,days,comments)
    
    is_approved = status == "ACCEPTED"
    label = "Approved" if is_approved else "Rejected"


    message = MessageSchema(
        subject=f"Your {leave_type} leave has been {label} - LeaveIQ",
        recipients=[employee_email],
        body=html,
        subtype="html"
    )
    await fm.send_message(message)


async def send_leave_cancelled_email(manager_email: str, employee_name: str, leave_type: str, from_date: str, to_date: str, days: int):
    html = f"""
    <div style="font-family: sans-serif; padding: 20px; color: #333;">
        <h2 style="color: #e11d48;">Leave Request Cancelled</h2>
        <p>Hello,</p>
        <p>This is to inform you that <strong>{employee_name}</strong> has cancelled their leave request for <strong>{leave_type}</strong>.</p>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <tr style="background-color: #f3f4f6;">
                <th style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">From Date</th>
                <td style="border: 1px solid #e5e7eb; padding: 8px;">{from_date}</td>
            </tr>
            <tr>
                <th style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">To Date</th>
                <td style="border: 1px solid #e5e7eb; padding: 8px;">{to_date}</td>
            </tr>
            <tr style="background-color: #f3f4f6;">
                <th style="border: 1px solid #e5e7eb; padding: 8px; text-align: left;">Total Days</th>
                <td style="border: 1px solid #e5e7eb; padding: 8px; font-weight: bold; color: #4f46e5;">{days}</td>
            </tr>
        </table>
        <p>Best regards,<br/><strong>LeaveIQ Team</strong></p>
    </div>
    """
    message = MessageSchema(
        subject=f"Leave Request Cancelled by {employee_name} - {leave_type} ({days} days)",
        recipients=[manager_email],
        body=html,
        subtype="html"
    )
    await fm.send_message(message)

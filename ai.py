import datetime
import json
from openrouter import OpenRouter

from config import OPENROUTER_API_KEY, OPENROUTER_MODEL


def get_openrouter_client():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is required")
    return OpenRouter(api_key=OPENROUTER_API_KEY)


def get_ai_recommendation(requested_days,leave_balance,reason):
    
    prompt = f"""
    Employee Leave Request

    Available Balance: {leave_balance}
    Requested Days: {requested_days}

    Reason:
    {reason}

    Give:
    Recommendation: Approve or Reject

    Explain in 2 lines.
    """
    with get_openrouter_client() as client:
        response = client.chat.send(
          model=OPENROUTER_MODEL,
          messages=[
            {
              "role": "user",
              "content": prompt
            }
          ]
        )
    
    return response.choices[0].message.content

def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()  # Converts to "YYYY-MM-DD" or "YYYY-MM-DDTHH:MM:SS"
    raise TypeError(f"Type {type(obj)} not serializable")

def get_weekly_summary(cursor):
    
    select_query = """
        SELECT * FROM leave_requests lr 
        JOIN employee e ON lr.employee_id = e.id 
        WHERE lr.created_at >= CURRENT_TIMESTAMP - INTERVAL 8 DAY;
    """
    
    cursor.execute(select_query)
    result=cursor.fetchall()
    json_string = json.dumps(result,default=json_serial)
    
    prompt = f"""
    You are an HR analytics assistant.

    Analyze the leave request data below.

    Return your response in this format:

    Total Requests: <number>

    Approved: <number>

    Rejected: <number>

    Pending: <number>

    Most Common Leave Type: <leave type>

    Observations:
    - observation 1
    - observation 2

    Executive Summary:
    <summary>

    Data:
    {json_string}
    
    Give it in json format
    
    Return ONLY valid JSON.

    Do not wrap the response in markdown.
    Do not use ```json.
    Do not provide any explanation outside the JSON.
    """
        
    with get_openrouter_client() as client:
        response = client.chat.send(
          model=OPENROUTER_MODEL,
          messages=[
            {
              "role": "user",
              "content": prompt
            }
          ],
          response_format={"type": "json_object"}
        )
    
    return response.choices[0].message.content

def getIntent(question):
    
    prompt = f"""
    User Question:

    {question}

    Return only one:

    leave_balance
    pending_requests
    last_leave_status
    unknown
    
    """
    
    
    
    with get_openrouter_client() as client:
        response = client.chat.send(
          model=OPENROUTER_MODEL,
          messages=[
            {
              "role": "user",
              "content": prompt
            }
          ]
        )
        
    return response.choices[0].message.content
  
  
def get_ai_apply_email(manager_email: str, employee_name: str, leave_type: str, from_date: str, to_date: str, days: int, reason: str):
  
  prompt = f"""
  You are an HR assistant.

  Generate a professional email to a manager informing them
  about a new leave request.

  Employee Name: {employee_name}
  Leave Type: {leave_type}
  From Date: {from_date}
  To Date: {to_date}
  Days: {days}
  Reason: {reason}

  Return only the email body in HTML format.
  """
  with get_openrouter_client() as client:
        response = client.chat.send(
          model=OPENROUTER_MODEL,
          messages=[
            {
              "role": "user",
              "content": prompt
            }
          ]
        )
        
  return response.choices[0].message.content


def get_ai_decision_email(employee_email: str, employee_name: str, status: str, leave_type: str, from_date: str, to_date: str, days: int, comments: str = ""):
  
  prompt = f"""
    You are a professional HR communication assistant for LeaveIQ.

    Generate a professional leave decision email for an employee.

    Employee Details:
    - Employee Name: {employee_name}
    - Leave Type: {leave_type}
    - From Date: {from_date}
    - To Date: {to_date}
    - Number of Days: {days}
    - Decision Status: {status}
    - Manager Comments: {comments}

    Requirements:
    1. Address the employee by name.
    2. Clearly mention whether the leave request was approved or rejected.
    3. Include leave type, dates, and duration.
    4. Mention manager comments if provided.
    5. Maintain a professional and friendly HR tone.
    6. Keep the email concise (150-200 words maximum).
    7. Return ONLY valid HTML content.
    8. Do NOT include <html>, <head>, or <body> tags.
    9. Do NOT include markdown or code blocks.
    10. Use simple HTML tags such as:
      - <div>
      - <h2>
      - <p>
      - <strong>

    Generate the email now.
    """
    
  with get_openrouter_client() as client:
        response = client.chat.send(
          model=OPENROUTER_MODEL,
          messages=[
            {
              "role": "user",
              "content": prompt
            }
          ]
        )
        
  return response.choices[0].message.content



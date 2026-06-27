import json

from openrouter import OpenRouter
from fastapi import FastAPI
from pydantic import BaseModel
from retriever import search_policy
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

app = FastAPI()
class RagAsk(BaseModel):
    question:str


def get_openrouter_client():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY environment variable is required")
    return OpenRouter(api_key=OPENROUTER_API_KEY)
    
@app.post("/rag")
def ai_search(chat:RagAsk):
    
    tools=[
        {
        "type":"function",
        "function":{
            "name": "search_leave_policy",
            "description": """
                Search the insurance policy document and retrieve
                relevant information about coverage, benefits,
                claims, exclusions, grace periods, policy termination,
                grievances, and other policy details.

                Use this tool whenever a question requires
                information from the insurance document.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string"
                    }
                },
                "required": ["question"]
            }
        }
    }
    ]
        
    with get_openrouter_client() as client:
        
        response = client.chat.send(
            model=OPENROUTER_MODEL,
            messages=[
                {
                    "role":"system",
                    "content":"""
                    You are an AI assistant for an insurance policy document.

                    Use the search_policy tool whenever the user asks about:
                    - policy coverage
                    - benefits
                    - claims
                    - premium payment
                    - grace period
                    - exclusions
                    - eligibility
                    - accidental death benefits
                    - claim procedures
                    - policy termination
                    - grievance procedures

                    Always use the tool before answering policy-related questions.

                    If information is not found in the document,
                    say "Information not found in policy."
                    """
                },
                {
                    "role":"user",
                    "content":chat.question
                }
            ],
            tools=tools
            )
        
    message=response.choices[0].message
    
    if not message.tool_calls:
        print("No Tools")
    
    tool_call=message.tool_calls[0]
    
    print(tool_call)
    
    tool_map = {
        "search_leave_policy":search_policy
    }
    args = json.loads(tool_call.function.arguments)
    
    function_name=tool_call.function.name
    
    result = tool_map[function_name](**args)
    
    print(result)
    
    prompt = f"""
        You are an expert insurance policy assistant.

        Answer ONLY using the provided context.

        Rules:
        1. Use all relevant context, even if information is spread across multiple sections.
        2. Preserve dates, deadlines, monetary amounts, and conditions exactly.
        3. Distinguish between different procedures and their timelines.
        4. If only partial information is available, answer with the available information.
        5. Do not infer or hallucinate facts.
        6. If the answer is absent, respond exactly:
        "Information not found in policy."

        Context:
        {result}

        Question:
        {chat.question}
    """
    with get_openrouter_client() as client:
        
        new_response = client.chat.send(
            model=OPENROUTER_MODEL,
            messages=[
                {
                "role": "user",
                "content": prompt
                }
            ],

            )
        
    return new_response.choices[0].message.content
    
    
    
    
    
    
    
    
        
    
    

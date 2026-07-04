import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Checks for a local testing file on your computer
load_dotenv()

app = FastAPI()

# Connects to the Groq backend client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class InterviewRequest(BaseModel):
    prompt: str

# UPDATED ROUTE DECORATOR TO MATCH SCRIPT.JS EXACTLY
@app.post("/groq")
async def handle_interview(request: InterviewRequest):
    try:
        # Request completion from Groq cloud
        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical interviewer. Always respond strictly in valid JSON format as requested."
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            response_format={"type": "json_object"} # Guarantees clean JSON output strings
        )
        
        ai_response = chat_completion.choices[0].message.content
        
        # Wrapped structure mimics your old Gemini logic perfectly
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": ai_response
                            }
                        ]
                    }
                }
            ]
        }
        
    except Exception as e:
        return {"error": str(e)}

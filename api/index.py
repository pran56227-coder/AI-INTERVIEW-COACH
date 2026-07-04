import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class InterviewRequest(BaseModel):
    prompt: str

# CHANGE THIS LINE TO JUST "/gemini"
@app.post("/gemini")
async def handle_interview(request: InterviewRequest):
    try:
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
            response_format={"type": "json_object"}
        )
        
        ai_response = chat_completion.choices[0].message.content
        
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

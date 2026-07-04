import os
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Automatically loads a local .env file if it exists on your machine
load_dotenv()

app = FastAPI()

# Groq automatically picks up the 'GROQ_API_KEY' environment variable
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class InterviewRequest(BaseModel):
    prompt: str

@app.post("/api/gemini") # Keeping this route identical means NO changes are needed in script.js!
async def handle_interview(request: InterviewRequest):
    try:
        # Call the Groq SDK using the highly reliable Llama 3.1 8B model
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
            response_format={"type": "json_object"} # Forces the model to output clean JSON
        )
        
        # Format the response payload so your frontend script.js reads it flawlessly
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

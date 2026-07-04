from http.server import BaseHTTPRequestHandler
import json
import os
from groq import Groq

# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 1. Read incoming request data cleanly
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        prompt = request_data.get('prompt', '')

        try:
            # 2. Query the Groq API
            chat_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert technical interviewer. Always respond strictly in valid JSON format as requested."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
            )
            ai_response = chat_completion.choices[0].message.content
            
            # 3. Construct the response object matching your frontend structure
            response_body = {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": ai_response}]
                        }
                    }
                ]
            }
            
            # 4. Return successful JSON response
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode('utf-8'))

        except Exception as e:
            # Handle any internal execution errors cleanly
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

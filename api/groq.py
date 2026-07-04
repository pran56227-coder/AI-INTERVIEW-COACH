from http.server import BaseHTTPRequestHandler
import json
import os
from groq import Groq

# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        prompt = request_data.get('prompt', '')

        # Check if this is a question generation request
        is_generation = "Generate 5 interview questions" in prompt

        # Adapt the system instructions to guarantee valid JSON object shapes
        if is_generation:
            system_prompt = (
                "You are an expert technical interviewer. You must generate 5 interview questions. "
                "Return your response strictly as a JSON object with a single key named 'questions' "
                "containing an array of strings. Example: {\"questions\": [\"Q1\", \"Q2\"]}"
            )
        else:
            system_prompt = (
                "You are an expert technical interviewer. Evaluate the user's answer. "
                "Return a JSON object containing keys: score, feedback, improvement, correct_answer."
            )

        try:
            # Query the Groq API
            chat_completion = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            ai_response = chat_completion.choices[0].message.content
            
            # TRANSLATION LAYER: Convert the object back into a flat array string for the frontend script
            if is_generation:
                try:
                    parsed_json = json.loads(ai_response)
                    if "questions" in parsed_json:
                        # Re-stringfy just the flat list element so script.js is completely happy
                        ai_response = json.dumps(parsed_json["questions"])
                except Exception:
                    pass # Fallback to original text if parsing fails

            # Construct the final response payload matching the frontend template structure
            response_body = {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": ai_response}]
                        }
                    }
                ]
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_body).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

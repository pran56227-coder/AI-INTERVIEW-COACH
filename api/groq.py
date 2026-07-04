from http.server import BaseHTTPRequestHandler
import json
import os
import re
from groq import Groq

# Initialize the Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        request_data = json.loads(post_data.decode('utf-8'))
        prompt = request_data.get('prompt', '')

        is_generation = "Generate 5 interview questions" in prompt

        if is_generation:
            system_prompt = (
                "You are an expert technical interviewer. Generate 5 interview questions. "
                "Return your response strictly as a JSON object with a single key named 'questions' "
                "containing an array of strings. Example: {\"questions\": [\"Q1\", \"Q2\"]}. "
                "Do not include any text outside the JSON object structure."
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
            
            ai_response = chat_completion.choices[0].message.content.strip()
            
            # --- FAIL-SAFE TRANSLATION & CLEANING LAYER ---
            if is_generation:
                # 1. Strip away any accidental markdown wrapping if present
                clean_text = re.sub(r"json|", "", ai_response).strip()
                
                try:
                    parsed_json = json.loads(clean_text)
                    if "questions" in parsed_json:
                        ai_response = json.dumps(parsed_json["questions"])
                    elif isinstance(parsed_json, list):
                        ai_response = json.dumps(parsed_json)
                except Exception:
                    # 2. Fallback: If it completely failed parsing, use Regex to find the first array structure [...]
                    array_match = re.search(r"\[\s*.?\s\]", clean_text, re.DOTALL)
                    if array_match:
                        ai_response = array_match.group(0)
                    else:
                        # 3. Double Fallback: Try to find a curly brace structure {...} and look for the list inside
                        object_match = re.search(r"\{\s*.?\s\}", clean_text, re.DOTALL)
                        if object_match:
                            try:
                                nested_json = json.loads(object_match.group(0))
                                for key in nested_json:
                                    if isinstance(nested_json[key], list):
                                        ai_response = json.dumps(nested_json[key])
                                        break
                            except Exception:
                                pass

            # Construct the final response payload matching your frontend structure
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

import requests
import json
import re
from config import GEMINI_API_KEY

def parse_gemini_output(output_text):
    """Parse Gemini output and convert to JSON."""
    match = re.search(r"```json(.*?)```", output_text, re.DOTALL)
    json_str = match.group(1).strip() if match else output_text.strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return {
            "label": "Unknown",
            "confidence": 0.0,
            "source": "",
            "explanation": output_text,
            "quiz": []
        }

def check_text(text):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY
    }

    prompt = f"""
You are a fact-checking AI.

Analyze the following news:
\"\"\"{text}\"\"\"

Tasks:
1. Determine if the news is True or Fake.
2. Provide a detailed explanation with sources.
3. Generate 10 unique multiple-choice quiz questions with 3 options each, and indicate the correct answer.
4. Return ONLY a valid JSON object in this format:
{{
  "label": "True/Fake",
  "confidence": 0.0-1.0,
  "source": "URL or text",
  "explanation": "Reason why news is true/fake",
  "quiz": [
    {{"question": "...", "options": ["...","...","..."], "answer": "..."}}
  ]
}}
Wrap the JSON inside triple backticks with "json" (```json ... ```).
"""

    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
    except requests.HTTPError as e:
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"API Error: {e}",
            "quiz": []
        }

    response_json = response.json()
    print("Full API response:", response_json)  # Debugging

    # Safely get the first candidate
    candidates = response_json.get("candidates")
    if not candidates or not isinstance(candidates, list):
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"No candidates returned. Full response: {response_json}",
            "quiz": []
        }

    first_candidate = candidates[0]
    if not isinstance(first_candidate, dict):
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"First candidate is not a dict. Full response: {response_json}",
            "quiz": []
        }

    # Safely get the text content
    content_dict = first_candidate.get("content")
    if not content_dict or not isinstance(content_dict, dict):
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"No content in candidate. Full response: {response_json}",
            "quiz": []
        }

    content_parts = content_dict.get("parts")
    if not content_parts or not isinstance(content_parts, list):
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"No parts in content. Full response: {response_json}",
            "quiz": []
        }

    first_part = content_parts[0]
    if not isinstance(first_part, dict) or "text" not in first_part:
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"No text in content part. Full response: {response_json}",
            "quiz": []
        }

    result_text = first_part.get("text", "")
    if not result_text:
        return {
            "label": "Error",
            "confidence": 0.0,
            "source": "",
            "explanation": f"Empty text returned. Full response: {response_json}",
            "quiz": []
        }

    # Parse JSON safely
    output_json = parse_gemini_output(result_text)
    return output_json

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
from models.fake_detection import check_text
import os
import requests
import json
import re
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests from Chrome extension
app.secret_key = "supersecret"  # Required for sessions

# -------------------------
# Helper function to maintain streak
# -------------------------
def update_streak():
    last_visit = session.get("last_visit")
    today = datetime.now().date()
    streak = session.get("streak", 0)

    if last_visit:
        last_visit_date = datetime.strptime(last_visit, "%Y-%m-%d").date()
        if last_visit_date == today - timedelta(days=1):
            streak += 1
        elif last_visit_date < today - timedelta(days=1):
            streak = 1
    else:
        streak = 1

    session["streak"] = streak
    session["last_visit"] = today.strftime("%Y-%m-%d")
    return streak

# -------------------------
# Home page
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    streak = update_streak()
    if request.method == "POST":
        user_text = request.form.get("news_text")
        if not user_text:
            return render_template("index.html", error="Please enter news text", streak=streak)

        result = check_text(user_text)
        session["result"] = result
        session["quiz"] = result.get("quiz", [])
        session["current_question"] = 0
        session["score"] = 0

        return redirect(url_for("analysis"))

    return render_template("index.html", streak=streak)

# -------------------------
# Analysis page
# -------------------------
@app.route("/analysis")
def analysis():
    if "result" not in session:
        return redirect(url_for("index"))
    return render_template("analysis.html", result=session["result"])

# -------------------------
# Quiz page
# -------------------------
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "quiz" not in session or not session["quiz"]:
        return redirect(url_for("index"))

    current_index = session.get("current_question", 0)
    quiz_list = session["quiz"]

    if current_index >= len(quiz_list):
        return redirect(url_for("result"))

    question = quiz_list[current_index]

    if request.method == "POST":
        selected = request.form.get("option")
        question["selected"] = selected
        question["is_correct"] = (selected == question["answer"])
        quiz_list[current_index] = question

        if selected == question["answer"]:
            session["score"] += 1

        session["current_question"] = current_index + 1
        if session["current_question"] >= len(quiz_list):
            return redirect(url_for("result"))
        return redirect(url_for("quiz"))

    return render_template(
        "quiz.html",
        question=question,
        current_q=current_index,
        total=len(quiz_list),
        score=session.get("score", 0),
        streak=session.get("streak", 0),
        show_final=False
    )

# -------------------------
# Result page
# -------------------------
@app.route("/result")
def result():
    if "result" not in session:
        return redirect(url_for("index"))

    return render_template(
        "result.html",
        result=session["result"],
        quiz=session.get("quiz", []),
        score=session.get("score", 0),
        streak=session.get("streak", 0),
        total=len(session.get("quiz", []))
    )

# -------------------------
# Gemini API settings
# -------------------------
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyD8bJo-Ym804WQ9KI65Hasmw6lSdgVCuhs")
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set!")

# -------------------------
# Analyze endpoint (for Chrome extension + API)
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text") if request.is_json else None
    if not text:
        return jsonify({"error": "No text provided"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500

    try:
        headers = {"Content-Type": "application/json"}
        params = {"key": GEMINI_API_KEY}

        # 🔹 Force Gemini to respond with structured JSON
        prompt = f"""
You are a fake news detection AI. Analyze the following text and respond ONLY in JSON.

Format:
{{
  "label": "Real" or "Fake" or "Unknown",
  "confidence": a float between 0 and 1,
  "explanation": "short explanation why you classified it"
}}

Text to analyze:
{text}
"""

        data = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(GEMINI_URL, headers=headers, params=params, json=data)
        api_response = response.json()

        # Extract raw text Gemini returned
        content = (
            api_response.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        ).strip()

        print("Full API response:", json.dumps(api_response, indent=2))
        print("Gemini content:", content)

        # Try parsing as JSON directly
        try:
            result_json = json.loads(content)
        except json.JSONDecodeError:
            # Fallback if Gemini wrapped in ```json ... ```
            match = re.search(r'```json(.*?)```', content, re.DOTALL)
            if match:
                try:
                    result_json = json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    result_json = None
            else:
                result_json = None

        # Default fallback if nothing parsable
        if not result_json:
            result_json = {
                "label": "Unknown",
                "confidence": 0,
                "explanation": content or "No explanation available"
            }

        return jsonify({
            "label": result_json.get("label", "Unknown"),
            "confidence": result_json.get("confidence", 0),
            "explanation": result_json.get("explanation", content),
            "input_text": text
        })

    except Exception as e:
        print("Error calling Gemini API:", e)
        return jsonify({"error": str(e)}), 500
# -------------------------
# Run the app
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)

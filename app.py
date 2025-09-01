from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
from models.fake_detection import check_text  # Make sure this exists
import os
import requests
import json
from flask_cors import CORS  # Needed for Chrome extension requests

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

        # Get Gemini result
        result = check_text(user_text)

        # Store in session
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

    result_data = session["result"]
    return render_template("analysis.html", result=result_data)

# -------------------------
# Quiz page
# -------------------------
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if "quiz" not in session or not session["quiz"]:
        return redirect(url_for("index"))

    current_index = session.get("current_question", 0)
    quiz_list = session["quiz"]

    # Finished all questions
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
        current_index += 1

        # Finished quiz
        if current_index >= len(quiz_list):
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

    result_data = session["result"]
    quiz_list = session.get("quiz", [])
    return render_template(
        "result.html",
        result=result_data,
        quiz=quiz_list,
        score=session.get("score", 0),
        streak=session.get("streak", 0),
        total=len(quiz_list)
    )

# -------------------------
# Gemini API key
# -------------------------
GEMINI_API_KEY = "AIzaSyD8bJo-Ym804WQ9KI65Hasmw6lSdgVCuhs"
# Alternatively, load from environment variable
GEMINI_API_KEY = os.environ.get("AIzaSyD8bJo-Ym804WQ9KI65Hasmw6lSdgVCuhs", GEMINI_API_KEY)
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not set!")

# -------------------------
# Analyze endpoint (for Chrome extension)
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form.get("text") or request.json.get("text")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    if not GEMINI_API_KEY:
        return jsonify({"error": "Gemini API key not configured"}), 500

    try:
        headers = {"Authorization": f"Bearer {GEMINI_API_KEY}"}
        data = {
            "prompt": text,
            "model": "gemini-2.0-flash",
            "max_output_tokens": 500
        }

        response = requests.post("https://api.openai.com/v1/responses", headers=headers, json=data)
        api_response = response.json()
        print("Full API response:", api_response)

        # Handle error from API
        if "error" in api_response:
            return jsonify({"error": api_response["error"]["message"]}), 500

        # Extract text
        if "candidates" in api_response:
            content = api_response["candidates"][0]["content"]["parts"][0]["text"]
        else:
            content = "No response from Gemini API"

        # Try to parse JSON inside content
        match = None
        import re
        match = re.search(r'```json(.*?)```', content, re.DOTALL)
        if match:
            result_json = json.loads(match.group(1).strip())
        else:
            result_json = {
                "label": "Unknown",
                "confidence": 0,
                "source": "N/A",
                "explanation": content
            }

        return jsonify({
            "label": result_json.get("label"),
            "confidence": result_json.get("confidence"),
            "source": result_json.get("source"),
            "explanation": result_json.get("explanation"),
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

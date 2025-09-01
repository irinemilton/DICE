# utils/quiz_generator.py
import random

def generate_quiz(text):
    # Example: simple 3-question quiz based on text
    questions = [
        {
            "question": "What type of news is this?",
            "options": ["Fake", "True", "Unknown"],
            "answer": "True" if "true" in text.lower() else "Fake"
        },
        {
            "question": "Is AI used in this news?",
            "options": ["Yes", "No", "Maybe"],
            "answer": "Yes"
        },
        {
            "question": "Should you trust the source?",
            "options": ["Yes", "No", "Depends"],
            "answer": "Depends"
        }
    ]
    random.shuffle(questions)
    return questions

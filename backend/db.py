import sqlite3
import google.generativeai as genai

def init_db():
    conn = sqlite3.connect("codesmart.db")
    c = conn.cursor()
    # Table for user progress (from previous response)
    c.execute('''CREATE TABLE IF NOT EXISTS user_progress
                 (user_id TEXT, problem_id TEXT, success BOOLEAN, timestamp TEXT)''')
    # Table for scraped problems
    c.execute('''CREATE TABLE IF NOT EXISTS problems
                 (problem_id TEXT PRIMARY KEY, title TEXT, url TEXT)''')
    conn.commit()
    conn.close()

def insert_problem(problem_id, title, url):
    conn = sqlite3.connect("codesmart.db")
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO problems (problem_id, title, url) VALUES (?, ?, ?)",
              (problem_id, title, url))
    conn.commit()
    conn.close()

def get_all_problems():
    conn = sqlite3.connect("codesmart.db")
    c = conn.cursor()
    c.execute("SELECT problem_id, title, url FROM problems")
    problems = [{"problem_id": row[0], "title": row[1], "url": row[2]} for row in c.fetchall()]
    conn.close()
    return problems

# Existing functions for user progress (from previous response)
def log_user_progress(user_id, problem_id, success):
    conn = sqlite3.connect("codesmart.db")
    c = conn.cursor()
    c.execute("INSERT INTO user_progress VALUES (?, ?, ?, datetime('now'))",
              (user_id, problem_id, success))
    conn.commit()
    conn.close()

def get_user_suggestions(user_id, problem_id, code_assistant, problem_statement, language):
    conn = sqlite3.connect("codesmart.db")
    c = conn.cursor()
    c.execute("SELECT success FROM user_progress WHERE user_id = ? AND problem_id = ?", (user_id, problem_id))
    results = c.fetchall()
    success_count = sum(1 for r in results if r[0])  # Count successful attempts for this problem
    attempt_count = len(results)  # Total attempts for this problem
    conn.close()

    # Determine the user's experience level based on attempts and success
    if attempt_count == 0:
        experience_level = "new to this problem"
    elif success_count > 0:
        experience_level = "has solved this problem before"
    else:
        experience_level = f"has made {attempt_count} unsuccessful attempts"

    # Use Gemini AI to generate a personalized suggestion
    prompt = (
        f"Generate a concise, personalized suggestion (5-6 lines) for a user solving the following coding problem: {problem_statement}. "
        f"The suggestion should be in {language} and help the user by providing guidance on how to approach the problem, considering their experience level. "
        f"The user {experience_level}. Focus on practical advice, such as key concepts to understand, a high-level strategy, or common pitfalls to avoid. "
        f"Do not provide a full solution or code, but rather actionable guidance to help the user progress."
    )

    try:
        response = code_assistant.generate_content(prompt)
        suggestion = response.text
        return suggestion
    except Exception as e:
        return f"Failed to generate suggestion: {str(e)}"
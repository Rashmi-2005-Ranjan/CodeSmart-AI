from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
from db import init_db, get_all_problems, log_user_progress, get_user_suggestions
import google.generativeai as genai
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from gtts import gTTS
import os
import uuid
import urllib.parse  # Added for URL encoding

GOOGLE_API_KEY = "AIzaSyDL4FzvADFGIxauzKO33m0t3p4VE3cvHGg"
genai.configure(api_key=GOOGLE_API_KEY)
code_assistant = genai.GenerativeModel("gemini-1.5-flash")

app = FastAPI()

# Ensure the static directory exists before mounting
if not os.path.exists("static"):
    os.makedirs("static")

# Serve static files (for audio files)
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to CodeSmart API! Available endpoints: /problems, /assist, /log_progress"}

init_db()

class ProblemRequest(BaseModel):
    problem_id: str
    user_code: str = None
    error_message: str = None
    request_type: str  # Now includes "hint", "solution", "suggestion", "explanation", "error_explanation", "code_insights", "learning_resources"
    user_id: str = "user123"
    problem_name: str = "Unknown Problem"  # Added problem_name to the request model

def scrape_leetcode_problem(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract the problem statement
        problem_statement = soup.find("div", class_="content__u3I1").text
        
        # Extract the problem title
        title_element = soup.find("div", class_="title__8lP8")
        problem_title = title_element.text.strip() if title_element else "Unknown Problem"
        # Remove the problem number prefix (e.g., "6. " in "6. Zigzag Conversion")
        problem_title = problem_title.split(". ", 1)[-1] if ". " in problem_title else problem_title
        
        return problem_statement, problem_title
    except Exception as e:
        return f"Failed to scrape problem statement: {str(e)}", "Unknown Problem"

def detect_language(code: str) -> str:
    code_lower = code.lower()
    if "hashmap" in code_lower or "public" in code_lower or "int[]" in code_lower:
        return "Java"
    elif "def " in code_lower or "range(" in code_lower or "print(" in code_lower:
        return "Python"
    else:
        return "Unknown"

def get_learning_resources(problem_id: str, problem_statement: str, problem_name: str) -> list:
    problems = get_all_problems()
    problem = next((p for p in problems if p["problem_id"] == problem_id), None)
    if not problem:
        return []

    # Use the user-provided problem_name instead of the scraped problem_title
    problem_name_formatted = urllib.parse.quote(problem_name)  # URL-encode the problem name

    resources = []

    # GeeksforGeeks search
    gfg_url = f"https://www.geeksforgeeks.org/search/{problem_name_formatted}/"
    resources.append({
        "url": gfg_url,
        "description": f"GeeksforGeeks: Search results for '{problem_name}', which may include articles on solving techniques, data structures, and algorithms relevant to this LeetCode problem."
    })

    # LeetCode problem page
    leetcode_url = problem.get("url", "")
    if leetcode_url:
        resources.append({
            "url": leetcode_url,
            "description": f"LeetCode: The official problem page for '{problem_name}' with the problem statement, constraints, examples, and a discussion forum where you can find community insights and explanations."
        })

    # Programiz search
    programiz_url = f"https://www.programiz.com/search/{problem_name_formatted}"
    resources.append({
        "url": programiz_url,
        "description": f"Programiz: Search results for '{problem_name}', which may include beginner-friendly tutorials on relevant data structures and algorithms."
    })

    # YouTube search
    youtube_url = f"https://www.youtube.com/results?search_query=leetcode+{problem_id}.+{problem_name_formatted}"
    resources.append({
        "url": youtube_url,
        "description": f"YouTube: Search results for video tutorials explaining '{problem_name}', often with visual walkthroughs and detailed explanations of solution approaches."
    })

    # Techie Delight search
    techie_delight_url = f"https://www.techiedelight.com/search/{problem_name_formatted}/"
    resources.append({
        "url": techie_delight_url,
        "description": f"Techie Delight: Search results for '{problem_name}', which may include articles on coding techniques and patterns useful for solving it."
    })

    return resources

@app.get("/problems")
async def list_problems():
    return get_all_problems()

@app.post("/assist")
async def assist(request: ProblemRequest):
    problems = get_all_problems()
    problem = next((p for p in problems if p["problem_id"] == request.problem_id), None)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Scrape both the problem statement and title
    problem_statement, problem_title = scrape_leetcode_problem(problem["url"])

    if request.request_type == "hint":
        prompt = f"Provide a concise hint for solving the following coding problem: {problem_statement}. Focus on a key concept or approach without giving the full solution. The hint should be applicable for a solution in Python."
        if request.user_code:
            prompt += f"\n\nThe user has provided the following code to consider while generating the hint:\n\npython\n{request.user_code}\n"
        try:
            response = code_assistant.generate_content(prompt)
            hint = response.text
            return {"hint": hint}
        except Exception as e:
            return {"error": f"Failed to generate hint: {str(e)}"}

    elif request.request_type == "solution":
        # Generate the text solution
        prompt = f"For the following coding problem: {problem_statement}, provide a solution as concise pseudocode (written in plain English, no programming language syntax like functions or brackets) that outlines the approach. Then, include two specific examples with input and output relevant to the problem to show how the solution works. Do not include any actual code (e.g., Python) or detailed explanations beyond the pseudocode and examples."
        if request.user_code:
            prompt += f"\n\nThe user has provided the following code to consider while generating the pseudocode:\n\npython\n{request.user_code}\n\nAdapt the pseudocode to align with the user's code if possible."
        try:
            response = code_assistant.generate_content(prompt)
            solution_text = response.text
        except Exception as e:
            return {"error": f"Failed to generate solution: {str(e)}"}

        # Convert the solution text to speech using gTTS
        try:
            # Generate a unique filename with UUID
            unique_id = str(uuid.uuid4())  # Ensure UUID is generated as a string
            audio_filename = f"solution_{request.problem_id}_{unique_id}.mp3"
            audio_filepath = os.path.join("static", audio_filename)
            print(f"Generating audio file: {audio_filepath}")  # Debug
            tts = gTTS(text=solution_text, lang="en")
            tts.save(audio_filepath)
            print(f"Audio file saved: {audio_filepath}, exists: {os.path.exists(audio_filepath)}")  # Debug
            if not os.path.exists(audio_filepath):
                raise Exception("Audio file was not created successfully")
            audio_url = f"/static/{audio_filename}"
        except Exception as e:
            print(f"Audio generation error: {str(e)}")  # Debug
            return {"error": f"Failed to generate voice solution: {str(e)}"}

        # Return both the text solution and the voice solution URL
        return {
            "solution": solution_text,
            "voice_solution_url": audio_url
        }

    elif request.request_type == "suggestion":
        suggestion = get_user_suggestions(
            user_id=request.user_id,
            problem_id=request.problem_id,
            code_assistant=code_assistant,
            problem_statement=problem_statement,
            language="python"
        )
        return {"suggestion": suggestion}

    elif request.request_type == "explanation":
        prompt = f"For the following coding problem: {problem_statement}, provide a detailed and elaborative explanation of what the problem is asking in plain English. Describe the problem's goal, its requirements, and any constraints or rules in a clear and thorough way, as if explaining it to someone new to programming. Do not include any code, pseudocode, examples, or solution strategies—just focus on explaining the problem itself."
        try:
            response = code_assistant.generate_content(prompt)
            explanation = response.text
            return {"explanation": explanation}
        except Exception as e:
            return {"error": f"Failed to generate explanation: {str(e)}"}

    elif request.request_type == "error_explanation":
        if not request.user_code or not request.error_message:
            raise HTTPException(status_code=400, detail="Both user_code and error_message are required for error_explanation")

        if "\n" in request.user_code and "\\n" not in request.user_code:
            raise HTTPException(status_code=400, detail="user_code contains unescaped newlines; please escape them as \\n")
        if "\n" in request.error_message and "\\n" not in request.error_message:
            raise HTTPException(status_code=400, detail="error_message contains unescaped newlines; please escape them as \\n")

        language = detect_language(request.user_code)
        if language == "Unknown":
            raise HTTPException(status_code=400, detail="Could not detect the programming language of the code")

        prompt = f"The user has provided the following {language} code:\n\n{request.user_code}\n\nAnd encountered this error message:\n\n{request.error_message}\n\nProvide a detailed explanation of what this error means in plain English, as if explaining to someone new to programming. Focus on why this error occurs in the context of the code and problem. Do not include any code snippets, pseudocode, or suggest fixes or solutions—just explain the error itself in words."
        try:
            response = code_assistant.generate_content(prompt)
            explanation = response.text
            return {"error_explanation": explanation}
        except Exception as e:
            return {"error": f"Failed to generate error explanation: {str(e)}"}

    elif request.request_type == "code_insights":
        if not request.user_code:
            raise HTTPException(status_code=400, detail="user_code is required for code_insights")

        language = detect_language(request.user_code)
        if language == "Unknown":
            raise HTTPException(status_code=400, detail="Could not detect the programming language of the code")

        prompt = f"The user has provided the following {language} code for the problem: {problem_statement}\n\n{request.user_code}\n\nProvide insights about the code in plain English, focusing on the following aspects:\n- Correctness: Assess whether the code is likely to produce the correct output for the problem, and identify any logical errors or issues that might cause it to fail.\n- Execution Time & Memory Usage: Assess how efficiently the code might run compared to other possible approaches, considering factors like loops, data structures, and memory allocation.\n- Big-O Complexity Estimation: Analyze the time complexity of the code (e.g., O(n), O(n^2)) and explain what this means.\n- Unnecessary Computations: Identify any redundant loops, repeated calculations, or unoptimized logic that could slow down the code.\nExplain these insights in a beginner-friendly way, as if talking to someone new to programming. Do not include any code snippets, pseudocode, or suggest fixes or solutions—just describe the insights in words"
        try:
            response = code_assistant.generate_content(prompt)
            insights = response.text
            return {"code_insights": insights}
        except Exception as e:
            return {"error": f"Failed to generate code insights: {str(e)}"}

    elif request.request_type == "learning_resources":
        resources = get_learning_resources(request.problem_id, problem_statement, request.problem_name)
        return {"learning_resources": resources}

    return {"error": "Invalid request type"}

@app.post("/log_progress")
async def log_progress(user_id: str, problem_id: str, success: bool):
    log_user_progress(user_id, problem_id, success)
    return {"message": "Progress logged successfully"}
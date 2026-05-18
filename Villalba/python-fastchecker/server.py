import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types

# 1. Force Python to load the .env file explicitly
load_dotenv()

app = Flask(__name__, static_folder='public')
CORS(app)

# 2. Get the key from the environment
api_key = os.getenv("GEMINI_API_KEY")

# 3. SAFETY CHECK: If it's still missing, tell us exactly why!
if not api_key:
    raise ValueError("CRITICAL: GEMINI_API_KEY is missing from your .env file or the server can't read it!")

# 4. Pass the key directly into the client initialization
client = genai.Client(api_key=api_key)

# Route 1: Serve your frontend HTML page to anyone visiting http://localhost:5002
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

# Route 2: Catch static assets like style.css and script.js
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

# Route 3: The Secure API Gateway - Users talk to this, hiding your key
@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        text_to_analyze = data.get('textToAnalyze')
        
        if not text_to_analyze:
            return jsonify({"error": "No text provided"}), 400

        structured_system_prompt = f"""
You are an advanced fact-checking AI with live internet access. Your job is to evaluate the credibility of the incoming text, claim, or URL.

CRITICAL WORKFLOW:
1. Identify the core news event or claim being made in the input.
2. Use your Google Search tool to search the live web for other mainstream articles, official government press releases, or source reporting matching this event.
3. Cross-reference what you find. Check if reputable, globally trusted news organizations (like Reuters, AP News, BBC, Bloomberg, etc.) are corroborating this exact story.

Provide your final output using this exact structure:
VERDICT: [REAL / FAKE / SATIRE / MISLEADING]
CONFIDENCE SCORE: [0% to 100%]
SUMMARY REASONING: [Provide a 2-sentence explanation summarizing what you found on the live web, specifically naming the sources.]

Incoming text or link to evaluate:
"{text_to_analyze}"
        """

        # Call Gemini securely using the official SDK with Google Search Grounding enabled
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=structured_system_prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}] # Gives the AI live web search powers
            )
        )

        return jsonify({"analysis": response.text})

    except Exception as e:
        print(f"Server Error: {e}")
        return jsonify({"error": "Failed to communicate with Gemini system."}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
from flask import Flask, request, jsonify, render_template
import os
import requests
import logging
import json

from dotenv import load_dotenv
from openai import OpenAI
from middleware.interface import chat_gpt

from util.util_ava.query_analysis import QueryAnalyzer
from util.util_ava.util_interface import AIInterface

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

# Load knowledge data
knowledge_data_path = os.path.join(os.path.dirname(__file__), 'resources', 'knowledge.txt')
if os.path.exists(knowledge_data_path):
    with open(knowledge_data_path, 'r', encoding='utf-8') as file:
        knowledge_data = file.read()
else:
    knowledge_data = ""

# Introductory message from Ava
AVA_INTRO_MESSAGE = "Hello! I'm Ava, here to support you in exploring 'A World.' How can I assist you today?"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not found"}), 500
    
    data = request.json
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing prompt"}), 400

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"model": "gpt-4", "messages": [
                {'role': 'system', 'content': knowledge_data},
                {"role": "user", "content": data['prompt']}
            ]}
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route('/chat_user', methods=['POST'])
def chat_user():
    print("Initializing AIInterface and QueryAnalyzer")

    try:
        ai_interface = AIInterface()
        query_analyzer = QueryAnalyzer(ai_interface)
    except Exception as e:
        print(f"Error during initialization: {e}")
        return jsonify({"error": f"Initialization error: {str(e)}"}), 500

    print("Validating headers")
    auth_header = request.headers.get("Authorization")
    content_type = request.headers.get("Content-Type")

    if not auth_header or not auth_header.startswith("Bearer "):
        print("Authorization header missing or invalid")
        return jsonify({"error": "Authorization header missing or invalid"}), 401
    if content_type != "application/json":
        print("Invalid Content-Type")
        return jsonify({"error": "Content-Type must be application/json"}), 400

    print("Extracting JSON data from request")
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        print(f"Invalid JSON format: {data}")
        return jsonify({"error": "Invalid JSON format, expected a dictionary"}), 400

    print("Validating parameters")
    query = data.get("query", "").strip()
    aname = data.get("aname", "").strip()
    user_profile = data.get("user_profile", "").strip()
    user_last_chat_history = data.get("user_last_chat_history", "").strip()

    # Logging missing parameters
    if not query:
        print("⚠️ Warning: 'query' is missing or empty.")
    if not aname:
        print("⚠️ Warning: 'aname' is missing or empty.")
    if not user_profile or user_profile.lower() == "undefined":
        print("⚠️ Warning: 'user_profile' is missing or invalid, defaulting to '{}'.")
        user_profile = "{}"
    if not user_last_chat_history or user_last_chat_history.lower() == "undefined":
        print("⚠️ Warning: 'user_last_chat_history' is missing or invalid, defaulting to None.")
        user_last_chat_history = None

    print(f"Processed Query: {query}, Name: {aname}, User Profile: {user_profile}, Last Chat History: {user_last_chat_history}")

    try:
        print("Calling analyze_query method")
        answer = query_analyzer.analyze_query(
            user_name=aname,
            query=query,
            last_n_conversations=user_last_chat_history,
            user_profile=user_profile
        )

        print(f"analyze_query returned: {answer}")
        return jsonify({"response": answer}), 200
    except Exception as e:
        print(f"Error during query analysis: {e}")
        return jsonify({"error": str(e)}), 500



@app.route('/update_user_profile', methods=['POST'])
def update_user_profile():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        logging.error(f"Invalid JSON format received: {data}")
        return jsonify({"error": "Invalid JSON format, expected a dictionary"}), 400

    query = data.get("query", "").strip()
    user_profile = data.get("user_profile", "").strip()

    # Log and handle missing values
    if not query:
        logging.warning("⚠️ Warning: 'query' is missing or empty.")
    if not user_profile or user_profile.lower() == "undefined":
        logging.warning("⚠️ Warning: 'user_profile' is missing or invalid, defaulting to '{}'.")
        user_profile = "{}"  # Default to empty JSON object

    try:
        ai_interface = AIInterface()
        updated_profile = ai_interface.update_user_profile(query, user_profile)

        # Convert updated profile back to JSON string before returning
        updated_profile_str = json.dumps(updated_profile, ensure_ascii=False)

        # Log updated user profile
        logging.info(f"✅ Updated User Profile: {updated_profile_str}")

        return jsonify({"updated_user_profile": updated_profile_str}), 200
    except Exception as e:
        logging.error(f"Error in /update_user_profile endpoint: {e}")
        return jsonify({"error": str(e)}), 500



@app.before_request
def log_request_info():
    print(f"Request Method: {request.method}, Endpoint: {request.path}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or fallback to 5000
    app.run(host='0.0.0.0', port=port)
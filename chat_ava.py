from flask import Flask, request, jsonify, render_template
import os
import requests
import logging
import json
import time

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
        print(f"⚠️ Warning: Invalid Content-Type: {content_type}")
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

    # Handle missing values
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

        # Ensure the response is not double-encoded
        if isinstance(answer, str):
            try:
                answer = json.loads(answer)  # If it's a double-encoded string, convert it
            except json.JSONDecodeError:
                pass  # If it's already a valid string, keep it as is

        print(f"analyze_query returned: {answer}")
        return jsonify({"response": answer}), 200
    except Exception as e:
        print(f"Error during query analysis: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/update_user_profile', methods=['POST'])
def update_user_profile():
    print("Validating headers")
    content_type = request.headers.get("Content-Type")

    if content_type != "application/json":
        logging.warning(f"⚠️ Warning: Invalid Content-Type: {content_type}")
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        logging.error("❌ Error: No JSON payload received. Logging request headers for debugging:")
        logging.error(f"Headers: {dict(request.headers)}")
        return jsonify({"error": "Invalid or missing JSON payload"}), 400

    query = data.get("query", "").strip()
    user_profile = data.get("user_profile", "").strip()

    if not query:
        logging.warning("⚠️ Warning: 'query' is missing or empty.")
    if not user_profile or user_profile.lower() == "undefined":
        logging.warning("⚠️ Warning: 'user_profile' is missing or invalid, defaulting to '{}'.")
        user_profile = "{}"

    try:
        ai_interface = AIInterface()
        max_retries = 3
        attempt = 0
        updated_profile = None

        while attempt < max_retries:
            raw_response = ai_interface.update_user_profile(query, user_profile)
            logging.info(f"🧠 Raw AI Response (Attempt {attempt + 1}): {raw_response}")

            if isinstance(raw_response, str) and raw_response.strip():
                try:
                    updated_profile = json.loads(raw_response)
                    if updated_profile:
                        break  
                except json.JSONDecodeError:
                    logging.error(f"❌ Error decoding AI response: {raw_response}")

            attempt += 1
            time.sleep(1)

        # If OpenAI fails after 3 retries, return the original user profile
        if not updated_profile:
            logging.warning("⚠️ OpenAI response was empty after 3 attempts. Returning original user profile.")
            updated_profile = json.loads(user_profile)

        # Convert JSON profile to text
        profile_text = convert_json_to_text(updated_profile)

        logging.info(f"✅ Final Updated User Profile:\n{profile_text}")

        return jsonify({"updated_user_profile": profile_text}), 200

    except Exception as e:
        logging.error(f"Error in /update_user_profile endpoint: {e}")
        return jsonify({"error": str(e)}), 500




def convert_json_to_text(user_profile_dict):
    """
    Converts a dictionary user profile into a human-readable text format.
    
    :param user_profile_dict: Dictionary representing the user profile
    :return: Formatted text version of the user profile
    """
    try:
        if not user_profile_dict or not isinstance(user_profile_dict, dict):
            logging.warning("⚠️ Warning: Received empty or invalid user profile dictionary. Returning default message.")
            return "User profile is currently empty or unavailable."

        profile_text = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in user_profile_dict.items()])
        return profile_text

    except Exception as e:
        logging.error(f"❌ Error converting user profile to text: {e}")
        return "Error formatting profile."



@app.before_request
def log_request_info():
    print(f"Request Method: {request.method}, Endpoint: {request.path}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or fallback to 5000
    app.run(host='0.0.0.0', port=port)
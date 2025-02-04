from flask import Flask, request, jsonify, render_template
import os
import requests
import logging
import json
import time

from dotenv import load_dotenv

from util.util_ava.query_analysis import QueryAnalyzer
from util.util_ava.util_interface import AIInterface
from util.util_ava.util_user_profile import UserProfiler

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
    logging.info("📌 [START] Processing /update_user_profile request")
    content_type = request.headers.get("Content-Type")

    # Validate Content-Type header
    if not content_type or "application/json" not in content_type:
        logging.warning(f"⚠️ Invalid Content-Type: {content_type}")
        return jsonify({"error": "Content-Type must be application/json"}), 400

    try:
        # Validate and extract JSON payload
        data = request.get_json()
        if not isinstance(data, dict):
            raise ValueError("Invalid JSON payload: expected a dictionary.")

        # Extract required parameters
        query = data.get("query", "").strip()
        user_profile = data.get("user_profile", "").strip()

        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        if not user_profile:
            logging.warning("⚠️ User profile is missing or invalid, defaulting to an empty string.")
            user_profile = ""

        logging.info("🧠 Initializing OpenAI client")
        user_profiler = UserProfiler()

        attempt = 0
        max_retries = 3
        updated_profile = None

        while attempt < max_retries:
            try:
                logging.info(f"🔄 Attempt {attempt + 1}: Sending request to OpenAI")
                raw_response = user_profiler.update_user_profile(query, user_profile, data.get("user_profile", ""))

                if not raw_response.strip():
                    logging.warning("⚠️ OpenAI returned an empty response.")
                    attempt += 1
                    if attempt >= max_retries:
                        break
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue

                try:
                    parsed_response = json.loads(raw_response.strip())
                except json.JSONDecodeError:
                    logging.warning("⚠️ OpenAI response is not valid JSON. Attempting custom parsing.")
                    parsed_response = parse_custom_response(raw_response.strip())

                if isinstance(parsed_response, dict):
                    logging.info("✅ Successfully parsed OpenAI response.")
                    updated_profile = parsed_response
                    break
                else:
                    logging.warning(f"⚠️ OpenAI response is not a dictionary: {parsed_response}")

            except Exception as e:
                logging.error(f"🚨 Error processing OpenAI response: {str(e)}")
                attempt += 1
                if attempt >= max_retries:
                    break
                time.sleep(2 ** attempt)  # Exponential backoff

        if not isinstance(updated_profile, dict):
            logging.warning("⚠️ OpenAI response was empty or invalid after 3 attempts. Returning original user profile.")
            updated_profile = {"user_profile": user_profile}

        updated_profile_str = convert_dict_to_string(updated_profile)
        updated_profile_str = data.get("user_profile", "")+";"+updated_profile_str
        logging.info(f"✅ Final Updated User Profile: {updated_profile_str}")
        logging.info("📌 [END] Successfully processed /update_user_profile request")
        return jsonify({"updated_user_profile": updated_profile_str}), 200

    except Exception as e:
        logging.error(f"🚨 Critical Error in /update_user_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500

def convert_json_to_text(user_profile_json):
    """
    Converts a user profile JSON dictionary to a human-readable text format.
    If the JSON is empty or invalid, returns a default message.
    """
    try:
        if not user_profile_json or not isinstance(user_profile_json, dict):
            logging.warning("⚠️ Warning: Received empty or invalid user profile dictionary. Returning default message.")
            return "User profile is currently empty or unavailable."
        
        return ";".join([f"{key.capitalize()}: {value}".replace('"', '').replace('{', '').replace('}', '') for key, value in user_profile_json.items()])
    
    except Exception as e:
        logging.error(f"❌ Error in convert_json_to_text: {e}")
        return "Error formatting profile."
    
def convert_dict_to_string(dictionary):
    """
    Converts a dictionary to a human-readable string format.
    If the dictionary is empty or invalid, returns a default message.
    """
    try:
        if not dictionary or not isinstance(dictionary, dict):
            logging.warning("⚠️ Warning: Received empty or invalid dictionary. Returning default message.")
            return "Dictionary is currently empty or unavailable."
        
        return ";".join([f"{key}:{value}" for key, value in dictionary.items()])
    
    except Exception as e:
        logging.error(f"❌ Error in convert_dict_to_string: {e}")
        return "Error formatting dictionary."

def convert_json_to_string(user_profile_json):
    """
    Converts a user profile JSON dictionary to a JSON string.
    If the JSON is empty or invalid, returns an empty JSON object string.
    """
    try:
        if not user_profile_json or not isinstance(user_profile_json, dict):
            logging.warning("⚠️ Warning: Received empty or invalid user profile dictionary. Returning empty JSON object string.")
            return "{}"
        
        return json.dumps(user_profile_json)
    
    except Exception as e:
        logging.error(f"❌ Error in convert_json_to_string: {e}")
        return "{}"


def parse_custom_response(response):
    """
    Parses a custom delimited response string into a dictionary.
    """
    try:
        # Split the response by semicolons and then by colons to create key-value pairs
        return dict(item.split(":") for item in response.split(";"))
    except Exception as e:
        logging.error(f"🚨 Error parsing custom response: {str(e)}")
        return {}

@app.before_request
def log_request_info():
    print(f"Request Method: {request.method}, Endpoint: {request.path}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from environment or fallback to 5000
    app.run(host='0.0.0.0', port=port)
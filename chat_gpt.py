from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
knowledge_data = open(os.path.join(os.path.dirname(__file__), 'resources', 'knowledge.txt'), 'r', encoding='utf-8').read()

# Introductory message from Ava
AVA_INTRO_MESSAGE = "Hello! I'm Ava, here to support you in exploring 'A World.' How can I assist you today?"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        # Provide the introductory message when the session starts (GET request)
        return jsonify({"message": AVA_INTRO_MESSAGE}), 200
    
    # Handle POST request
    auth_header = request.headers.get("Authorization")
    content_type = request.headers.get("Content-Type")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or invalid"}), 401
    if content_type != "application/json":
        return jsonify({"error": "Content-Type must be application/json"}), 400

    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"response": "Please provide a prompt to start the conversation."})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {'role': 'system', 'content': knowledge_data },
                {"role": "user", "content": prompt}]
        )
        return jsonify({"response": response.choices[0].message.content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.before_request
def log_request_info():
    print(f"Request Method: {request.method}, Endpoint: {request.path}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from Render or fallback to 5000
    app.run(host='0.0.0.0', port=port)

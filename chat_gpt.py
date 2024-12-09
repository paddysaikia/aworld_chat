from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define assistant ID
assistant_id = "asst_oLLZnPCn5tRCcRANB2Il93KB"

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "OK"}), 200

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        return jsonify({"message": "This endpoint only supports POST requests."}), 405  # Method Not Allowed
    
    # Validate headers
    auth_header = request.headers.get("Authorization")
    content_type = request.headers.get("Content-Type")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or invalid"}), 401
    if content_type != "application/json":
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Handle POST request
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    try:
        # Use the assistant ID for chat completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            assistant_id=assistant_id,
            messages=[{"role": "user", "content": prompt}]
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

from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Step 1: Create an Assistant
assistant = client.beta.assistants.create(
    name="My Assistant",
    instructions="You are a helpful assistant that provides detailed responses.",
    model="gpt-4-1106-preview"
)
assistant_id = assistant.id
print(f"Assistant created with ID: {assistant_id}")

# Step 2: Create a Thread
thread = client.beta.threads.create(
    title="Initial Conversation"  # Optional title
)
thread_id = thread.id
print(f"Thread created with ID: {thread_id}")

# Step 3: Add a User Message to the Thread
message = client.beta.threads.messages.create(
    thread_id=thread_id,
    role="user",
    content="What can you do for me?"
)
print(f"User message added: {message.content}")

# Step 4: Generate a Run to Get Assistant Response
run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assistant_id  # This connects the thread with the assistant
)
print(f"Assistant response: {run.message.content}")

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
        # Step 2: Create a Thread
        thread = client.beta.threads.create(
            assistant_id=assistant_id,
            title="Conversation with User"
        )
        thread_id = thread.id
        print(f"Thread created with ID: {thread_id}")

        # Step 3: Add a User Message to the Thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=prompt
        )
        print(f"User message added: {message.content}")

        # Step 4: Generate a Run to Get Assistant Response
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id
        )
        assistant_response = run.message.content
        print(f"Assistant response: {assistant_response}")

        return jsonify({"response": assistant_response})
    except Exception as e:
        app.logger.error(f"Chat endpoint failed: {e}")
        return jsonify({"error": "Internal server error occurred"}), 500



@app.before_request
def log_request_info():
    print(f"Request Method: {request.method}, Endpoint: {request.path}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Use PORT from Render or fallback to 5000
    app.run(host='0.0.0.0', port=port)

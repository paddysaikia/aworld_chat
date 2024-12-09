from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        response = client.chat.completions.create(
            model="gpt-4o-mini",
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



# from openai import OpenAI
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# # Initialize the OpenAI client with your API key from the environment variable
# api_key = os.getenv("OPENAI_API_KEY")
# if not api_key:
#     raise ValueError("OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")
# client = OpenAI(api_key=api_key)

# def chat_with_gpt(prompt):
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",  # Replace with your desired model
#             messages=[{"role": "user", "content": prompt}]
#         )
#         return response.choices[0].message["content"]
#     except Exception as e:
#         return f"Error: {e}"

# if __name__ == "__main__":
#     print("ChatGPT CLI")
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() in ['exit', 'quit']:
#             print("Goodbye!")
#             break
#         response = chat_with_gpt(user_input)
#         print(f"GPT: {response}")

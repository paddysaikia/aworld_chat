from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app and OpenAI client
app = Flask(__name__)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables.")
client = OpenAI(api_key=api_key)

# Custom GPT model ID from environment
custom_model_id = os.getenv("CUSTOM_GPT_MODEL", "gpt-4o-mini")  # Default to "gpt-4o-mini" if not provided


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify service is running."""
    return jsonify({"status": "OK"}), 200


@app.route('/')
def home():
    """Serve the main page."""
    return render_template('index.html')


@app.route('/chat', methods=['POST', 'GET'])
def chat():
    """Chat endpoint for interacting with the custom GPT model."""
    if request.method == 'GET':
        return jsonify({"message": "This endpoint only supports POST requests."}), 405  # Method Not Allowed
    
    # Validate headers
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Authorization header missing or invalid"}), 401
    
    content_type = request.headers.get("Content-Type")
    if content_type != "application/json":
        return jsonify({"error": "Content-Type must be application/json"}), 400

    # Parse and validate request body
    data = request.json
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    try:
        # Call the custom GPT model
        response = client.chat.completions.create(
            model=custom_model_id,
            messages=[{"role": "user", "content": prompt}]
        )
        # Return the response
        return jsonify({"response": response.choices[0].message.content})
    except openai.error.InvalidRequestError as e:
        # Handle invalid model errors
        app.logger.error(f"Invalid GPT model ID: {custom_model_id}. Error: {str(e)}")
        return jsonify({"error": "Invalid GPT model ID. Please check your configuration."}), 400
    except Exception as e:
        # Log error and return a generic message
        app.logger.error(f"Error while processing GPT response: {str(e)}")
        return jsonify({"error": "An error occurred while processing your request. Please try again later."}), 500



@app.before_request
def log_request_info():
    """Log information about incoming requests."""
    app.logger.info(f"Request Method: {request.method}, Endpoint: {request.path}")
    app.logger.info(f"Using GPT model: {custom_model_id}")


if __name__ == '__main__':
    # Determine the port and run the app
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

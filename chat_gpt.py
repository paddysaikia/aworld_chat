from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route('/')
def home():
    return "ChatGPT API is running. Access the `/chat` endpoint to send requests."

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get("prompt", "")
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return jsonify({"response": response.choices[0].message["content"]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)



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
from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os

class ChatGPTClient:
    def __init__(self):
        # Initialize the OpenAI client with the API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key for OpenAI is missing. Set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully.")

    def generate_response(self, system_context, prompt):
        try:
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {'role': 'system', 'content': system_context},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error in ChatGPTClient: {e}")
            return {"error": str(e)}

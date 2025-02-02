from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import os
import json
import logging
import time

class ChatGPTClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key for OpenAI is missing. Set the OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        print("OpenAI client initialized successfully.")

    def generate_response(self, system_context, prompt):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {'role': 'system', 'content': system_context},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            except Exception as e:
                logging.error(f"OpenAI API error (attempt {attempt + 1}): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
        return json.dumps({"error": "Failed to get response from OpenAI."})

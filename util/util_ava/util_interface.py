import json
import logging
from middleware.interface.chat_gpt import ChatGPTClient

class AIInterface:
    def __init__(self):
        self.chat_client = ChatGPTClient()
        self.system_context = "You are an assistant specializing in analyzing and processing queries for A World."

    def send_initial_query(self, payload):
        print("Sending initial query")
        system_context = f"""
        {self.system_context}
        You will determine relevant tasks, sources, and inputs for the user's query. 
        Respond strictly in the following JSON format:
        {{
            "relevant_tasks": {{}},
            "relevant_sources": {{}},
            "relevant_inputs": {{}}
        }}
        Do not include any explanatory text or formatting outside this JSON format.
        """
        prompt = f"Analyze the following payload: {payload}."

        max_retries = 5
        attempt = 0

        while attempt < max_retries:
            response = self.chat_client.generate_response(system_context, prompt)
            print(f"Attempt {attempt + 1}: Raw response from send_initial_query:", response)

            # Clean and extract JSON
            parsed_response = clean_response(response)
            if parsed_response:
                print("Parsed response from send_initial_query:", parsed_response)
                return parsed_response

            # Retry with a stronger prompt
            print(f"Retrying... Attempt {attempt + 2}")
            attempt += 1

        # If all retries fail
        print("Failed to get a valid response after maximum retries.")
        return {"error": "Invalid initial query response from AI."}



    def send_refined_query(self, payload):
        print("Sending refined query")
        system_context = f"{self.system_context} You are refining a query for a deeper response based on the provided inputs. Ensure your response is strictly in this JSON format: {{\"response\": \"Final answer to the initial query\"}}. Do not include any additional text."
        prompt = f"Refine and process this payload: {payload}. Your response should only be in this JSON format: {{\"response\": \"Final answer to the initial query\"}}"

        max_retries = 5  # Maximum attempts to get the desired response format
        attempt = 0

        while attempt < max_retries:
            response = self.chat_client.generate_response(system_context, prompt)
            print(f"Attempt {attempt + 1}: Raw response from send_refined_query:", response)

            # Ensure the response is a string
            if isinstance(response, str):
                # Clean up response formatting and attempt to extract JSON
                response = response.strip("```json").strip("```").strip()

                # Find the JSON part in the response
                json_start = response.find("{")
                if json_start != -1:
                    response = response[json_start:]  # Extract from the first curly brace

                # Attempt to parse the cleaned response
                try:
                    response_dict = json.loads(response)
                    print(f"Parsed response from send_refined_query (Attempt {attempt + 1}):", response_dict)

                    # Check if the response is in the desired format
                    if "response" in response_dict and isinstance(response_dict["response"], str):
                        print("Response is in the desired format.")
                        return response_dict  # Return the valid response
                    else:
                        print("Response is not in the desired format.")
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in send_refined_query (Attempt {attempt + 1}): {e}")
            
            # Update the prompt to reinforce the strict JSON requirement
            prompt = f"{system_context} Ensure your response is strictly in this JSON format: {{\"response\": \"Final answer to the initial query\"}}. Do not include any other keys or formatting."
            attempt += 1

        # If the desired response format is not obtained after max_retries
        print("Failed to get a valid response in the desired format after 5 attempts.")
        return {"response": "Sorry, I was not able to understand you. Can you try that again?"}
    

    def update_user_profile(self, query, user_profile):
        """
        Updates the user profile based on relevant information extracted from the query.

        :param query: The user's query containing potential profile updates.
        :param user_profile: The current user profile data in JSON string format.
        :return: Updated user profile as a JSON string.
        """
        import json
        try:
            # Convert user_profile from JSON string to dictionary
            if isinstance(user_profile, str):
                user_profile = json.loads(user_profile) if user_profile.strip() else {}

            # Define system prompt to extract relevant new information
            system_prompt = (
                "Identify relevant personal information in the user's query that is not already in the user profile. "
                "Provide a simplified summary of this new information. Respond only in JSON format with key-value pairs "
                "for each new relevant detail. If no new relevant details are found, return an empty JSON object {}."
            )

            # Convert user_profile to string for AI processing
            user_profile_str = json.dumps(user_profile, ensure_ascii=False)

            # Use ChatGPTClient to analyze query for new profile updates
            extracted_info = self.chat_client.generate_response(system_prompt, f"User Profile: {user_profile_str}\nQuery: {query}")

            # Validate extracted_info before attempting to parse it
            if not extracted_info.strip():
                logging.warning("ChatGPT returned an empty response. Returning original user profile.")
                return json.dumps(user_profile, ensure_ascii=False)

            # Parse AI response
            try:
                extracted_info = json.loads(extracted_info)
            except json.JSONDecodeError as e:
                logging.error(f"Error decoding AI response: {e}. Returning original profile.")
                return json.dumps(user_profile, ensure_ascii=False)

            # If new relevant information is found, manually append it to the user profile
            if isinstance(extracted_info, dict) and extracted_info:
                user_profile.update(extracted_info)

            # Convert updated profile back to JSON string before returning
            return json.dumps(user_profile, ensure_ascii=False)

        except Exception as e:
            logging.error(f"Error updating user profile: {e}")
            return json.dumps(user_profile, ensure_ascii=False)  # Return original profile in case of failure

def clean_response(response):
    """
    Cleans the AI response to extract and parse the JSON part.
    """
    print("Raw response:", response)

    # Find the JSON part
    json_start = response.find("{")
    if json_start == -1:
        print("No JSON found in response.")
        return None

    json_part = response[json_start:]  # Extract from the first curly brace
    try:
        return json.loads(json_part)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

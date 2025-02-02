import json
import logging
from middleware.interface.chat_gpt import ChatGPTClient

class UserProfiler:
    def __init__(self):
        """
        Initialize the AI interface with a chat client and system context.
        """
        self.chat_client = ChatGPTClient()
        self.system_context = (
            "You are an assistant specializing in analyzing and processing queries for A World. "
            "Your task is to extract relevant personal information from user queries and update the user profile."
        )

    def update_user_profile(self, query, user_profile, user_profile_str):
        """
        Updates the user profile based on relevant information extracted from the query.

        :param query: The user's query containing potential profile updates.
        :param user_profile: The current user profile data in JSON string format.
        :return: Updated user profile as a JSON string.
        """
        try:
            print("Starting update_user_profile method")
            # Validate and parse the user profile
            print("Validating user profile")
            # if isinstance(user_profile, str):
            #     try:
            #         user_profile = json.loads(user_profile) if user_profile.strip() else {}
            #     except json.JSONDecodeError:
            #         logging.warning("Invalid JSON format for user profile string. Defaulting to an empty dictionary.")
            #         user_profile = {}
            # print(f"Parsed user profile: {user_profile}")

            if not isinstance(user_profile, dict):
                logging.warning("Invalid user profile format. Defaulting to an empty dictionary.")
                user_profile = {}
            print(f"Validated user profile: {user_profile}")

            # Define the system prompt
            print("Defining system prompt")
            system_prompt = (
                f"{self.system_context} Identify relevant personal information in the user's query "
                "that is not already in the user profile. Provide a simplified summary of this new information. "
                "Respond only in JSON format with key-value pairs for each new relevant detail. "
                "If no new relevant details are found, return an empty JSON object {}."
            )
            print(f"System prompt: {system_prompt}")

            # # Convert user profile to string for AI processing
            # print("Converting user profile to string")
            # user_profile_str = json.dumps(user_profile, ensure_ascii=False)
            # print(f"User profile string: {user_profile_str}")

            # Send query to ChatGPTClient
            print("Sending query to ChatGPTClient")
            print("complete prompt",f"User Profile: {user_profile_str}\nQuery: {query}\n{system_prompt}")
            ai_response = self.chat_client.generate_response("",f"User Profile: {user_profile_str}\nQuery: {query}\n{system_prompt}"            )
            print(f"AI response: {ai_response}")
            ai_response = ai_response.replace("```json", "").replace("```", "").strip()
            ai_response = ai_response.replace("'", '"')  # Ensure proper JSON format with double quotes
            print(ai_response)
            print(type(ai_response))
            # Validate the AI response
            print("Validating AI response")
            if not ai_response.strip():
                logging.warning("⚠️ ChatGPT returned an empty response. Returning original user profile.")
                return json.dumps(user_profile, ensure_ascii=False)
            print("AI response validated")

            try:
                # Parse the AI response as JSON
                print("Parsing AI response as JSON")
                extracted_info = json.loads(ai_response)
                print(f"Extracted info: {extracted_info}")
            except json.JSONDecodeError as e:
                logging.error(f"❌ Error decoding AI response: {e}. AI response: {ai_response}. Returning original user profile.")
                return json.dumps(user_profile, ensure_ascii=False)

            # Update the user profile with extracted information
            print("Updating user profile with extracted information")
            if isinstance(extracted_info, dict) and extracted_info:
                user_profile.update(extracted_info)
                logging.info(f"✅ Successfully updated user profile: {extracted_info}")
            else:
                logging.info("No new relevant information found in the AI response.")
            print(f"Updated user profile: {user_profile}")

            # Return the updated profile as a JSON string
            print("Returning updated user profile as JSON string")
            return json.dumps(user_profile, ensure_ascii=False)

        except Exception as e:
            logging.error(f"🚨 Unexpected error in update_user_profile: {e}")
            return json.dumps(user_profile, ensure_ascii=False)  # Return original profile on failure

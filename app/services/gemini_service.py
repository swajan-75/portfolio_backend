import json
import os
import google.generativeai as genai
from google.api_core import exceptions
from app.core.config import settings

class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
      
        json_path = os.path.join(os.path.dirname(__file__), "..", "core", "context.json")
        with open(json_path, "r") as f:
            data = json.load(f)
        
        
        self.context = self._format_context(data)

      
        self.model = genai.GenerativeModel(
            model_name="gemini-3-flash-preview", 
            system_instruction=self.context
        )

    def _format_context(self, data: dict) -> str:
        """Helper to flatten the structured JSON into a string for the AI."""
        identity = data["assistant_identity"]
        user = data["user_profile"]
        
        # We use a f-string to build the primary persona
        prompt = (
            f"Identity: Your name is {identity['name']}, the {identity['role']}. "
            f"Tone: {', '.join(identity['tone'])}.\n\n"
            f"Background: You represent {user['full_name']}, a {user['profession']} with a "
            f"{user['education']['degree']} in {user['education']['major']} from {user['education']['university']}.\n"
            f"Location: {user['location']['current_city']} (Home: {user['location']['home_town']}).\n\n"
            f"Technical Profile (Skills & Projects):\n{json.dumps(data['core_skills'], indent=2)}\n"
            f"Key Projects:\n{json.dumps(data['key_projects'], indent=2)}\n\n"
            f"Availability: {data['availability']['primary_hours']['start']} - {data['availability']['primary_hours']['end']} "
            f"({data['availability']['primary_hours']['timezone']}). Contact via {data['contact_information']['phone']}.\n\n"
            f"Guidelines: {data['response_scope']['restricted_topics_handling']}. "
            f"{data['response_scope']['extra_information_policy']}."
        
        )
        return prompt

    async def get_chat_response(self, user_message: str) -> str:
        try:
           
            response = self.model.generate_content(user_message)
            return response.text
        
        except exceptions.ResourceExhausted:
            return "I'm currently resting my circuits (Quota exceeded). Please try again in about a minute!"
        
        except Exception as e:
            return f"Jarves encountered a glitch: {str(e)}"
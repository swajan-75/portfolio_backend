import json
import os
from google import genai
from google.genai import types
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
        identity = data["assistant_identity"]
        user = data["user_profile"]

        prompt = (
            f"You are {identity['name']}, {identity['role']}.\n"
            f"Tone: {', '.join(identity['tone'])}.\n\n"
        
            # Suppress the Rick & Morty character behavior explicitly
            f"IMPORTANT: Do NOT say 'Look at me!', do NOT give dramatic introductions, "
            f"do NOT act like the cartoon character. You share the name but behave professionally.\n\n"
        
            f"You represent {user['full_name']}, a {user['profession']}. "
            f"Degree: {user['education']['degree']} in {user['education']['major']} from {user['education']['university']}. "
            f"Based in {user['location']['current_city']}.\n\n"
        
            f"Skills:\n{json.dumps(data['core_skills'], indent=2)}\n"
            f"Projects:\n{json.dumps(data['key_projects'], indent=2)}\n\n"
        
            f"Availability: {data['availability']['primary_hours']['start']} - "
            f"{data['availability']['primary_hours']['end']} ({data['availability']['primary_hours']['timezone']}). "
            f"Contact: {data['contact_information']['phone']}.\n\n"
        
            f"Rules:\n"
            f"- Keep all replies SHORT (2-3 sentences max for simple questions).\n"
            f"- NEVER use markdown, asterisks, bold, bullet points, or any formatting symbols.\n"
            f"- For off-topic questions, redirect briefly to Swajan's professional profile.\n"
            f"- For greetings or small talk, reply in one casual sentence and offer to help.\n"
            f"- {data['response_scope']['restricted_topics_handling']}.\n"
        )
        return prompt

    async def get_chat_response(self, user_message: str) -> str:
        try:
           
            response = self.model.generate_content(user_message)
            return response.text
        
        except exceptions.ResourceExhausted:
            return "I'm currently resting my circuits (Quota exceeded). Please try again in about a minute!"
        
        except Exception as e:
            return f"Mr. Meeseeks encountered a glitch: {str(e)}"
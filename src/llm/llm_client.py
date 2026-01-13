from google import genai
import os
from dotenv import load_dotenv

load_dotenv()


class LlmClient:
    def __init__(self, api_key: str = None):
        """
        Initializes the connection to Google Gemini.
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = "gemini-2.5-flash"

    @property
    def is_active(self) -> bool:
        """
        Checks if the LLM client is properly configured.
        """
        return self.model is not None

    def get_subprocess_name(self, activities, subprocess_id):
        """
        Sends a list of activities to Gemini and requests a semantic label.
        """
        if not self.model:
            return f"Subprocess {subprocess_id} (No API Key)"

        try:
            prompt = (
                f"You are a Business Process Analyst. "
                f"I have a cluster of process activities: {', '.join(activities)}. "
                f"Based on these activities, suggest a SHORT, professional name (max 4 words) "
                f"that describes this specific phase of the process. "
                f"Return ONLY the name, nothing else."
            )

            response = self.client.models.generate_content(
                model=self.model, contents=prompt
            )

            if response.text:
                return response.text.strip()
            else:
                return f"Subprocess {subprocess_id}"

        except Exception:
            return f"Subprocess {subprocess_id} (API Error)"

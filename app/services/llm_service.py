import google.generativeai as genai
import os

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment variables")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def summarize(self, title: str, description: str) -> str:
        if not description:
            return f"{title}. No description available."
        prompt = f"Summarize this news article in 2 sentences:\n\nTitle: {title}\n\nDescription: {description}"
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"[Gemini ERROR] {e}")
            return "Summary generation failed."

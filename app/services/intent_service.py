import google.generativeai as genai
import os, json, re

class IntentService:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("❌ GEMINI_API_KEY not found.")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def extract_intent(self, query: str) -> dict:
        """
        Use Gemini to extract structured information about the user's intent and entities.
        """
        prompt = f"""
        You are an intelligent intent extraction assistant for a contextual news retrieval system.

        Each article in the database has the following fields:
        - title
        - description
        - category (e.g., Technology, Business, Sports)
        - source_name (e.g., Reuters, BBC, Times Now)
        - publication_date
        - relevance_score
        - latitude, longitude (for location-based filtering)

        Analyze the following user query and determine:
        1. "intent": one or more of ['category', 'score', 'source', 'search', 'nearby']
        - 'category' → filter by category (Technology, Business, etc.)
        - 'source'   → filter by source name (Reuters, Times Now, etc.)
        - 'score'    → request for high relevance or top stories
        - 'search'   → general topic/keyword search
        - 'nearby'   → filter by location proximity
        2. "entities": list of detected entities (topics, people, organizations, or keywords)
        3. "location": location name if explicitly or implicitly mentioned (city, region, country)

        Respond ONLY with valid JSON, no text or code blocks.

        Examples:

        Query: "Show me top technology news from Times Now"
        Response:
        {{"intent": ["category", "news", "search"], "entities": ["Technology", "Times Now"], "location": null, "source": "Times Now"}}

        Query: "What are the latest political updates near Delhi?"
        Response:
        {{"intent": ["category", "nearby"], "entities": ["Politics"], "location": "Delhi"}}

        Query: "News about Elon Musk"
        Response:
        {{"intent": ["search"], "entities": ["Elon Musk"], "location": null}}

        Query: "Russia Ukraine war updates as reported by Reuters"
        Response:
        {{"intent": ["war", "updates"], "entities": ["Russia", "Ukraine", "war"], "location": "Russia", "source": "Reuters"}}

        Now analyze this query:
        "{query}"
        """

        try:
            resp = self.model.generate_content(prompt)
            text = resp.text.strip()
            # Clean and parse JSON safely
            text = re.sub(r"```(json)?", "", text)
            result = json.loads(text)
            return result
        except Exception as e:
            print(f"[Intent ERROR] {e}")
            # Default fallback
            return {"intent": ["search"], "entities": [], "location": None, "source": None}

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()


class LocationAnalyzer:
    """Second AI component that converts location text into latitude/longitude.
    
    Runs in parallel with the main Gemini analyzer using a separate API key.
    Its sole purpose is rapid geo-resolution of emergency locations.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY_2") or os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("[LocationAI] Warning: No API key found.")
            self.client = None

        self.system_instruction = (
            "You are a precise geocoding AI. Given a location description from an emergency call, "
            "return ONLY a JSON object with exactly two keys: \"latitude\" (float) and \"longitude\" (float). "
            "If the location is ambiguous, return your best estimate for the most likely coordinates. "
            "If the location is completely unresolvable, return {\"latitude\": null, \"longitude\": null}. "
            "Return ONLY valid JSON, no extra text."
        )

    def resolve_coordinates(self, location_text: str) -> tuple:
        """Convert a location description to (latitude, longitude).
        
        Returns (None, None) on failure.
        """
        if not location_text or not self.client:
            return None, None

        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Resolve this emergency location to coordinates: {location_text}",
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text)
            lat = data.get("latitude")
            lon = data.get("longitude")
            if lat is not None and lon is not None:
                return float(lat), float(lon)
        except Exception as e:
            print(f"[LocationAI] Error resolving coordinates: {e}")

        return None, None

import os
import json
import threading
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

TEMP_JSON = "temp.json"


class GeminiAnalyzer:
    """Main Gemini AI that extracts structured emergency data from conversation."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            print("[GeminiAnalyzer] Warning: GEMINI_API_KEY not found.")
            self.client = None

        self._file_lock = threading.Lock()

        self.system_instruction = (
            "You are an emergency response AI analyzing emergency phone transcriptions. "
            "Extract ALL the following keys into a strict JSON object (use null if unknown):\n"
            "- emergency_category\n- emergency_sub_type\n- incident_description\n"
            "- reporter_type\n- caller_name\n- caller_contact_number\n- caller_gender\n"
            "- state\n- district_city\n- locality_area\n- pin_code\n"
            "- severity_level (Critical / High / Medium / Low)\n"
            "- threat_to_human_life (Yes / No / Unknown)\n"
            "- number_of_casualties (integer)\n- number_of_injuries (integer)\n"
            "- weapon_hazard_involved\n"
            "- dispatch_needed (boolean)\n- dispatch_reason\n"
            "- system_reply (Generate a helpful, short, spoken response to the caller asking for missing critical info like location, or confirming help is on the way.)\n"
            "Return ONLY valid JSON."
        )

    def analyze_conversation(self, conversation_history: list) -> dict | None:
        """Analyze transcript lines and return a structured dict. Also writes to temp.json."""
        if not conversation_history or not self.client:
            return None

        text_to_analyze = "\n".join(conversation_history)
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=text_to_analyze,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    response_mime_type="application/json",
                ),
            )
            data = json.loads(response.text)
            data["conversation_history"] = conversation_history

            # Write intermediate result to temp.json
            self._write_temp(data)
            return data
        except Exception as e:
            print(f"[GeminiAnalyzer] Error: {e}")
            return None

    def _write_temp(self, data: dict):
        """Thread-safe write of the latest extraction to temp.json."""
        with self._file_lock:
            try:
                with open(TEMP_JSON, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"[GeminiAnalyzer] Could not write temp.json: {e}")

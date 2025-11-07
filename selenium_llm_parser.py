import re
import json
from typing import Tuple, List, Optional

from langchain_ollama import OllamaLLM
from data_generator import TestDataGenerator



def parse_selenium_script(script_text: str) -> Tuple[List[dict], Optional[str]]:

    script_text = script_text or ''
    llm = OllamaLLM(model="llama3:latest", temperature=0.0)
    parse_prompt = (
        "You are a parsers assistant. Given the following Selenium script (Python or JS), extract all form fields present in the page interactions.\n"
        "Return ONLY a JSON array. Each item must be an object with keys: name (snake_case), type (one of string,email,phone,pan,ifsc,account_number,postal_code,city,state,address,number,date), rules (short string or empty), description (one-sentence), example (one realistic example).\n"
        "Do not include any commentary or text outside the JSON array.\n\n"
        "Selenium script:\n" + script_text
    )

    try:
        resp = llm.invoke(parse_prompt)
        json_match = re.search(r'\[.*\]', resp, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = resp.strip()

        # Use TestDataGenerator's cleaning utilities for common LLM formatting issues
        cleaner = TestDataGenerator()
        json_str = cleaner._clean_json_response(json_str)

        parsed = json.loads(json_str)
        # ensure list of dicts
        if not isinstance(parsed, list):
            parsed = [parsed]
        # normalize items to required keys
        normalized = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            normalized.append({
                'name': item.get('name', '').strip(),
                'type': item.get('type', 'string'),
                'rules': item.get('rules', '') or '',
                'description': item.get('description', '') or '',
                'example': item.get('example', '') or ''
            })
        return normalized, None
    except Exception as e:
        return [], f"LLM parsing failed: {str(e)}"
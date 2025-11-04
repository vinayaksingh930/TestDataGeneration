
from langchain_ollama import OllamaLLM
import json
import re


class TestDataGenerator:
    
    def __init__(self, model_name: str = "llama3:latest"):
        self.llm = OllamaLLM(model=model_name, temperature=0.7)

    def _create_prompt(
        self, 
        schema_fields: list, 
        num_records: int, 
        correct_num_records: int, 
        wrong_num_records: int, 
        additional_rules: str = None, 
        parent_tables_data: dict = None
    ) -> str:
        
        field_names = [field.get('name', '') for field in schema_fields if field.get('name')]
        valid_count = correct_num_records
        invalid_count = wrong_num_records

        # Build field details with type, rules, and examples
        field_details = []
        for field in schema_fields:
            field_info = f"- {field.get('name', 'unknown')}: type={field.get('type', 'string')}"
            if field.get('rules'):
                field_info += f", rules={field.get('rules')}"
            if field.get('example'):
                field_info += f", example={field.get('example')}"
            field_details.append(field_info)
        
        # Build parent tables context
        parent_tables_context = ""
        if parent_tables_data:
            parent_tables_context = "\n                === PARENT TABLES DATA (USE THESE ACTUAL VALUES!) ===\n\n"
            for parent_table_name, parent_rows in parent_tables_data.items():
                parent_tables_context += f"                {parent_table_name.upper()} Table (already generated):\n"
                # Show sample of parent data with all fields
                sample_count = min(10, len(parent_rows))
                for i, row in enumerate(parent_rows[:sample_count]):
                    parent_tables_context += f"                  {row}\n"
                if len(parent_rows) > sample_count:
                    parent_tables_context += f"                  ... and {len(parent_rows) - sample_count} more records\n"
                parent_tables_context += "\n"
                
                # Extract key values for easy reference
                if parent_rows:
                    # Get all field names from first row
                    sample_row = parent_rows[0]
                    for key in sample_row.keys():
                        if key != "is_valid":
                            values = [str(row.get(key, "")) for row in parent_rows if key in row]
                            unique_values = list(set(values))[:20]  # Show up to 20 unique values
                            parent_tables_context += f"                Available {parent_table_name}.{key} values: {', '.join(unique_values)}\n"
                parent_tables_context += "\n"

        prompt = f"""You are an expert test data generator and validator. Your task is to generate {num_records} UNIQUE, DIVERSE, and REALISTIC test data records.

                SCHEMA DEFINITION:
                {chr(10).join(field_details)}

                {f"ADDITIONAL CONTEXT/RULES:\n{additional_rules}\n" if additional_rules else ""}
                {parent_tables_context}
                === CRITICAL INSTRUCTIONS ===

                1. DATA DIVERSITY & UNIQUENESS:
                - Every record must have COMPLETELY UNIQUE values — no repetition of any field value across records.
                - All values must look realistic and natural.
                - Never copy or reuse any example or previously generated value.
                - Each valid and invalid record must differ clearly from the others.
                {f"- **CRITICAL**: If parent table data is provided above, you MUST use those ACTUAL values (e.g., actual department names, actual IDs) to maintain referential integrity and logical consistency between tables." if parent_tables_data else ""}

                2. RECORD COUNT:
                - Generate EXACTLY {num_records} total records.
                - First {valid_count} records → STRICTLY VALID (is_valid = true)
                - Next {invalid_count} records → CLEARLY INVALID (is_valid = false)
                - Maintain this exact order in output.

                3. STRUCTURE:
                - Each record must include ALL {len(field_names)} fields: {', '.join(field_names)}
                - Plus one extra field: "is_valid" (boolean)
                - No missing or extra fields are allowed.

                4. VALID RECORDS (is_valid = true):
                - Must PERFECTLY follow all schema rules and types.
                - Follow the examples and constraints exactly:
                    * Length → respect min/max
                    * Type → match the specified type (e.g., string, number, email)
                    * Format → correct domain, correct pattern
                    * Range → within allowed bounds
                - Ensure these look realistic and production-like.

                5. INVALID RECORDS (is_valid = false):
                - Each invalid record must CLEARLY break at least ONE rule from the schema.
                - DO NOT make invalid records that still appear valid.
                - Randomly mix and diversify violation types:
                    * Wrong type (number instead of string, malformed email, etc.)
                    * Too short or too long value (length violation)
                    * Wrong domain (for emails), or invalid phone number length
                    * Missing required field value (empty or null)
                    * Nonsensical or unrealistic value
                - Each invalid record must fail for a *different reason*.
                - Ensure violations are OBVIOUS (e.g., wrong email format, phone not 10 digits, etc.)
                - No two invalid records should have the same type of error.

                6. OUTPUT REQUIREMENTS - CRITICAL:
                - Output MUST be a SINGLE JSON array ONLY — absolutely NO markdown, NO code blocks, NO explanations, NO comments, NO double brackets.
                - DO NOT wrap output in ```json or ``` or any code fence.
                - DO NOT add comments with // or /* */ inside the JSON.
                - DO NOT include any text before or after the JSON array.
                - DO NOT use double brackets ([[ ... ]]) — output a single array ([ ... ]) only.
                - DO NOT include trailing commas before closing brackets.
                - DO NOT repeat any value in any field, even between valid and invalid records.
                - Start your response directly with [ and end with ]
                - Each record must be a valid JSON object with proper commas and quotes.
                - Values must be unique and realistic.
                - Example structure:
                [
                {{ {', '.join([f'"{name}": "valid_value_example_{i+1}"' for i, name in enumerate(field_names)])}, "is_valid": true }},
                {{ {', '.join([f'"{name}": "invalid_value_example_{i+1}"' for i, name in enumerate(field_names)])}, "is_valid": false }}
                ]

                7. QUALITY CHECK BEFORE OUTPUT:
                - Verify that valid records follow all schema rules exactly.
                - Verify that invalid records visibly violate at least one rule.
                - Verify that NO value repeats anywhere.
                - Output ONLY the final JSON array.

                Now, generate {num_records} unique records following the above schema and constraints."""

        return prompt

    def _clean_json_response(self, response: str) -> str:
        # Remove double brackets
        response = re.sub(r'^\s*\[\s*\[', '[', response)
        response = re.sub(r'\]\s*\]\s*$', ']', response)
        
        # Remove comments
        response = re.sub(r'//.*', '', response)
        response = re.sub(r'/\*.*?\*/', '', response, flags=re.DOTALL)
        
        # Remove trailing commas before closing bracket
        response = re.sub(r',(\s*\])', r'\1', response)
        
        # Remove blank lines
        response = '\n'.join([line for line in response.splitlines() if line.strip()])
        
        # Remove lone 'null' tokens that appear as standalone entries inside objects
        # e.g. { "a": 1, null, "b": 2 } -> { "a": 1, "b": 2 }
        response = re.sub(r',\s*null\s*,', ',', response)
        response = re.sub(r',\s*null\s*}', '}', response)
        response = re.sub(r'{\s*null\s*,', '{', response)

        # Collapse accidental multiple commas introduced by fixes
        response = re.sub(r',\s*,+', ',', response)

        return response

    def generate_data(
        self, 
        schema_fields: list, 
        num_records: int = 5, 
        correct_num_records: int = 5, 
        wrong_num_records: int = 0, 
        additional_rules: str = None, 
        parent_tables_data: dict = None
    ) -> dict:
        try:
            # Create prompt
            prompt = self._create_prompt(
                schema_fields, 
                num_records, 
                correct_num_records, 
                wrong_num_records, 
                additional_rules, 
                parent_tables_data
            )

            print(f"\n--- PROMPT SENT TO LLM ---")
            print(prompt)
            print(f"--- END PROMPT ---\n")

            # Generate data using Ollama
            response = self.llm.invoke(prompt)

            print(f"\n--- LLM RESPONSE ---")
            print(response)
            print(f"--- END RESPONSE ---\n")

            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Try to fix incomplete response
                json_str = response.strip()
                if json_str.startswith('[') and not json_str.endswith(']'):
                    json_str += '\n]'
                json_str = re.sub(r',(\s*\])', r'\1', json_str)
            
            # Clean JSON
            json_str = self._clean_json_response(json_str)

            print(f"\n--- CLEANED JSON ---")
            print(json_str)
            print(f"--- END CLEANED JSON ---\n")

            # Parse JSON (try a second repair pass if initial parse fails)
            try:
                generated_data = json.loads(json_str)
            except json.JSONDecodeError:
                # Attempt additional, aggressive fixes for common LLM formatting issues
                repaired = json_str
                # Replace single quotes with double quotes when safe (only for simple cases)
                # but avoid changing common apostrophes by limiting to patterns of keys
                repaired = re.sub(r"(?<=[{,\s])'([^']+?)'\s*:\s*", r'"\1": ', repaired)
                # Ensure true/false/null are lowercase JSON literals (some LLMs use True/False/None)
                repaired = re.sub(r"\bTrue\b", 'true', repaired)
                repaired = re.sub(r"\bFalse\b", 'false', repaired)
                repaired = re.sub(r"\bNone\b", 'null', repaired)
                # Remove any remaining lone 'null' tokens
                repaired = re.sub(r',\s*null\s*,', ',', repaired)
                repaired = re.sub(r',\s*null\s*}', '}', repaired)
                repaired = re.sub(r'{\s*null\s*,', '{', repaired)
                repaired = re.sub(r',\s*,+', ',', repaired)

                print("\n--- REPAIRED JSON ATTEMPT ---")
                print(repaired)
                print("--- END REPAIRED JSON ATTEMPT ---\n")

                # Try parsing repaired JSON
                generated_data = json.loads(repaired)

            # Ensure it's a list
            if not isinstance(generated_data, list):
                generated_data = [generated_data]
            
            return {
                "data": generated_data[:num_records],
                "count": len(generated_data[:num_records])
            }
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON. LLM response format issue: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating data: {str(e)}")
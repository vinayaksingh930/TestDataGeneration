from langchain_ollama import OllamaLLM
import json
import re


class TestDataGenerator:
    
    def __init__(self, model_name: str = "llama3.2"):
        self.llm = OllamaLLM(model=model_name, temperature=0.7)
    
    def _create_prompt(self, schema_fields: list, num_records: int, additional_rules: str = None) -> str:
        prompt = f"""Generate exactly {num_records} realistic test data records based on the following schema:

        Schema: {json.dumps(schema_fields, indent=2)}

        {f"Additional Context: {additional_rules}" if additional_rules else ""}

        IMPORTANT INSTRUCTIONS:
        1. Return ONLY a valid JSON array of objects
        2. Each object must have ALL the specified fields from the schema
        3. Follow the data types and rules exactly as specified in the schema
        4. Make the data realistic and diverse
        5. If examples are provided in the schema, use them as guidance but create variations
        6. DO NOT include any explanatory text, markdown, or code blocks - only the raw JSON array

        Output must be a valid JSON array starting with [ and ending with ].

        Generate the data now:"""
        
        return prompt

    def generate_data(self, schema_fields: list, num_records: int = 5, additional_rules: str = None) -> dict:
        try:
            # Create prompt
            prompt = self._create_prompt(schema_fields, num_records, additional_rules)
            
            # Generate data using Ollama
            response = self.llm.invoke(prompt)
            
            # Parse JSON response
            # Clean the response to extract JSON
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response
            
            generated_data = json.loads(json_str)
            
            # Ensure it's a list
            if not isinstance(generated_data, list):
                generated_data = [generated_data]
            
            return {
                "data": generated_data[:num_records],
                "count": len(generated_data[:num_records])
            }
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse generated data as JSON. LLM response might not be in correct format: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating data: {str(e)}")

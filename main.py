from fastapi import FastAPI, HTTPException
from data_generator import TestDataGenerator
from langchain_ollama import OllamaLLM
import json

app = FastAPI(title="Test Data Generator API")


# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Test Data Generator API"
    }


@app.get("/health")
async def health_check():
    try:
        # Test Ollama connection
        llm = OllamaLLM(model="llama3.2")
        llm.invoke("test")
        return {"status": "healthy", "ollama": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/generate")
async def generate_test_data(request: dict):
    try:
        # Extract request parameters
        schema_fields = request.get("schema_fields", [])
        num_records = request.get("num_records", 5)
        additional_rules = request.get("additional_rules")
        
        # Validate required fields
        if not schema_fields:
            raise HTTPException(
                status_code=400,
                detail="schema_fields is required and cannot be empty"
            )
        
        # Generate data
        generator = TestDataGenerator()
        result = generator.generate_data(
            schema_fields=schema_fields,
            num_records=num_records,
            additional_rules=additional_rules
        )
        
        return {
            "data": result["data"],
            "count": result["count"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error: {str(e)}"
        ) 
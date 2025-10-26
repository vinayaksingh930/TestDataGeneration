from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from data_generator import TestDataGenerator
from langchain_ollama import OllamaLLM
import json

app = FastAPI(title="Test Data Generator API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        llm = OllamaLLM(model="qwen3-vl:235b-cloud")
        llm.invoke("test")
        return {"status": "healthy", "ollama": "connected", "model": "qwen3-vl:235b-cloud"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/generate")
async def generate_test_data(request: dict):
    try:
        #print("Received request:", request)
        # Extract request parameters
        schema_fields = request.get("schema_fields", [])
        num_records = request.get("num_records", 5)
        correct_num_records = request.get("correct_num_records", 5)
        wrong_num_records = request.get("wrong_num_records", 0)
        additional_rules = request.get("additional_rules")

        print("Schema fields:", schema_fields)
        print("Number of records:", num_records)
        print("Number of correct records:", correct_num_records)
        print("Number of wrong records:", wrong_num_records)
        print("Additional rules:", additional_rules)

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
            correct_num_records=correct_num_records,
            wrong_num_records=wrong_num_records,
            additional_rules=additional_rules
        )
        
        #print("Generated data:", result)

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
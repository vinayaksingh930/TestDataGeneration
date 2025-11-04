"""
Test Data Generator API

FastAPI backend for generating realistic test data using LangChain + Ollama.
Supports both single table and multi-table database generation with intelligent agents.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from data_generator import TestDataGenerator
from db_generator import DatabaseTestDataGenerator
from intelligent_db_generator import IntelligentDatabaseGenerator
from nl_db_generator import NaturalLanguageDatabaseGenerator
from langchain_ollama import OllamaLLM

app = FastAPI(title="Test Data Generator API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {"message": "Test Data Generator API - Ready"}


@app.get("/health")
async def health_check():
    try:
        llm = OllamaLLM(model="llama3:latest")
        llm.invoke("test")
        return {
            "status": "healthy", 
            "ollama": "connected", 
            "model": "llama3:latest"
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e)
        }


@app.post("/generate")
async def generate_test_data(request: dict):
    try:
        # Extract parameters
        schema_fields = request.get("schema_fields", [])
        num_records = request.get("num_records", 5)
        correct_num_records = request.get("correct_num_records", 5)
        wrong_num_records = request.get("wrong_num_records", 0)
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
            correct_num_records=correct_num_records,
            wrong_num_records=wrong_num_records,
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


@app.post("/generate-db")
async def generate_database(request: dict):
    try:
        db_schema = request.get("db_schema")
        
        if not db_schema:
            raise HTTPException(
                status_code=400,
                detail="db_schema is required"
            )
        
        tables = db_schema.get("tables", [])
        if not tables:
            raise HTTPException(
                status_code=400,
                detail="At least one table is required in db_schema"
            )
        
        # Validate each table
        for i, table in enumerate(tables):
            if not table.get("table_name"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Table at index {i} is missing 'table_name'"
                )
            if not table.get("fields"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Table '{table.get('table_name')}' is missing 'fields'"
                )
        
        # Choose generator based on mode
        use_intelligent = db_schema.get("use_intelligent_mode", True)
        
        if use_intelligent:
            print("Using INTELLIGENT mode with AI agents")
            generator = IntelligentDatabaseGenerator()
        else:
            print("Using MANUAL mode (requires explicit PK/FK)")
            generator = DatabaseTestDataGenerator()
        
        result = generator.generate_database(db_schema)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating database: {str(e)}"
        )


@app.post("/generate-from-text")
async def generate_from_natural_language(request: dict):
    try:
        user_text = request.get("user_text", "").strip()
        
        if not user_text:
            raise HTTPException(
                status_code=400,
                detail="user_text is required and cannot be empty"
            )
        
        if len(user_text) < 20:
            raise HTTPException(
                status_code=400,
                detail="Please provide a more detailed description (at least 20 characters)"
            )
        
        print(f"NATURAL LANGUAGE GENERATION REQUEST")
        
        # Generate database from natural language
        generator = NaturalLanguageDatabaseGenerator()
        result = generator.generate_from_text(user_text)
        
        print(f"\nNatural language generation completed successfully!")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error generating from natural language: {str(e)}"
        ) 
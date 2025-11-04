"""
# Test Data Generator — Full Project Documentation

This repository implements an intelligent test-data generation system capable of producing realistic, diverse, and referentially-correct test data for single tables and multi-table databases. It uses a small multi-agent architecture backed by a local LLM (Ollama) to parse requirements, design schemas, infer relationships, and generate records.

This document covers:
- Quick start (run & test)
- Detailed API reference for every endpoint in `main.py`
- Data shapes (request/response JSON)
- Agent internals and responsibilities (all back-end agents)
- Data flow and generation lifecycle
- Troubleshooting, configuration and tuning
- Recent fixes and developer notes

## Quick Start

Prerequisites
- Python 3.9+ (this repo uses Python 3.13 in the provided virtualenv)
- Node.js 16+ (for frontend)
- Ollama installed and a local model available (e.g., `llama3:latest`)

Start backend (example using the included virtualenv):

```bash
cd /Users/vinayak/Desktop/Watermelon/TestData
source myenv/bin/activate
python -m uvicorn main:app --reload --port 8001
```

Start frontend (if using `test-data-frontend`):

```bash
cd test-data-frontend
npm install
npm start
```

Health check: GET http://127.0.0.1:8001/health — verifies LLM connectivity.

## High-level Architecture

Frontend (React) → FastAPI backend (`main.py`) → Multi-agent orchestrators → LLM (Ollama)

- `main.py`: HTTP API, validation, entry points
- `data_generator.py`: Single-table generation using LLM prompts
- `db_generator.py` / `intelligent_db_generator.py`: Multi-table orchestration (PK/FK handling, topo-sort, injection, validation)
- `nl_db_generator.py`: Natural-language pipeline (text->schema->relationships->generation)

All LLM calls are proxied via a small wrapper (`langchain_ollama`) so you can replace or configure the model easily.

## API Reference (endpoints in `main.py`)

All endpoints accept and return JSON. The server will raise HTTP 400 for client errors or HTTP 500 for unexpected failures.

### GET /
Simple readiness endpoint.

Response example:
```json
{ "message": "Test Data Generator API - Ready" }
```

### GET /health
Performs a minimal LLM invocation to check that Ollama is reachable.

Response (healthy):
```json
{ "status": "healthy", "ollama": "connected", "model": "llama3:latest" }
```

If the LLM cannot be contacted this returns an `unhealthy` status with `error` text describing the problem.

### POST /generate
Single-table generation endpoint.

Request JSON shape:
```json
{
  "schema_fields": [
    { "name": "email", "type": "email", "rules": "valid format" },
    { "name": "age", "type": "integer", "rules": "18-99" }
  ],
  "num_records": 10,
  "correct_num_records": 8,
  "wrong_num_records": 2,
  "additional_rules": "Optional extra rules for the LLM"
}
```

Behavior:
- Validates `schema_fields` is present and non-empty.
- Calls `TestDataGenerator.generate_data(...)` which:
  - Builds a detailed LLM prompt describing field types, rules, parent table context (if provided) and strict output rules (JSON-only).
  - Invokes the LLM and attempts to parse a JSON array from the response.
  - Applies JSON-cleaning heuristics and a repair pass for common LLM formatting issues before finally parsing.

Response example:
```json
{
  "data": [ {"email":"a@example.com","age":25,"is_valid":true}, ... ],
  "count": 10
}
```

Errors:
- 400 if `schema_fields` missing.
- 500 if the generator or LLM fails to produce parseable JSON after repair attempts.

### POST /generate-db
Full multi-table database generation.

Request JSON shape (top-level `db_schema` object required):
```json
{
  "db_schema": {
    "db_name": "my_db",
    "use_intelligent_mode": true,
    "tables": [
      {
        "table_name": "departments",
        "num_records": 5,
        "correct_num_records": 5,
        "wrong_num_records": 0,
        "additional_context": "Optional human-readable context",
        "fields": [
          { "name": "name", "type": "string" },
          { "name": "building", "type": "string" }
        ]
      },
      {
        "table_name": "employees",
        "num_records": 20,
        "correct_num_records": 18,
        "wrong_num_records": 2,
        "fields": [
          { "name": "name", "type": "string" },
          { "name": "email", "type": "email" },
          { "name": "dept_id", "type": "integer", "references": {"table":"departments","field":"Department_id"} }
        ]
      }
    ]
  }
}
```

Behavior (high-level pipeline, implemented in `IntelligentDatabaseGenerator.generate_database`):
1. Preprocessing: normalize names and remove duplicate fields.
2. Primary Key Detection: `PrimaryKeyDetectionAgent` ensures each table has a primary key (table-specific name, e.g., `department_id`). If none found, it inserts an auto-generated integer PK.
3. Foreign Key Detection: `ForeignKeyDetectionAgent` scans existing fields to identify fields likely to be FKs (e.g., `dept_id`, `department`), marking `references` on those fields.
4. Schema Enhancement: `SchemaEnhancementAgent` suggests new FK fields if a relationship exists semantically but no explicit FK field is present; the agent may add fields like `employee_id` or `department_id` and mark their `references`.
5. Relationship Inference: `RelationshipInferenceAgent` adds per-table generation rules (business logic hints) used by the LLM when producing records for realism.
6. Topological Sorting: `_topo_sort_tables` (Kahn's algorithm) determines generation order. If a cycle is detected the system logs the cycle and produces a best-effort order rather than crashing.
7. Data Generation: For each table in order, `TestDataGenerator.generate_data` is used to generate fields (PKs are synthesized, FKs are injected from parent tables). Parent table values are passed to the child LLM prompts to increase realism.
8. Foreign Key Injection: `_inject_foreign_keys` populates FK fields from parent table keys for valid records and injects invalid FK values for invalid records. Injection skips fields that would overwrite a table's primary key (prevents PK collisions).
9. Validation: `DataValidationAgent` checks referential integrity and other constraints and returns a validation report.

Response example (success):
```json
{
  "db_name": "my_db",
  "tables": { "departments": [...], "employees": [...] },
  "counts": { "departments": {"total":5,"valid":5,"invalid":0}, "employees": {"total":20,"valid":18,"invalid":2} },
  "generation_order": ["departments","employees"],
  "primary_keys": {"departments":"Department_id","employees":"Employee_id"},
  "validation": { "overall_valid": true, "errors": [], "warnings": [] }
}
```

Errors:
- 400 if `db_schema` is missing or malformed (missing `tables` or `table_name` or `fields`).
- 500 on LLM or unexpected errors — traceback printed to server logs.

### POST /generate-from-text
Natural Language Mode: provide a free-text description and the system will create a complete database schema and data.

Request example:
```json
{ "user_text": "Create a college database with departments, employees, and salaries. Departments should have name and building. Employees belong to departments. Generate 5 departments, 20 employees, and 20 salaries." }
```

High-level flow (implemented in `nl_db_generator.py` — `NaturalLanguageDatabaseGenerator`):
1. Text Parsing (`TextParserAgent`) — extracts `db_name`, `tables` (+ any `explicit_fields`), `num_records`, and `relationship` hints from the free text using the LLM.
2. Schema Design (`SchemaDesignerAgent`) — for each table, infers 5–10 appropriate fields (types, examples) and returns a field list (explicit fields are preserved). This agent is instructed not to add PKs or FKs.
3. Relationship Detection (`RelationshipDetectorAgent`) — given the parsed tables and relationship hints, returns suggested FK fields and the tables they reference.
4. Schema Validation (`SchemaValidatorAgent`) — performs checks (min fields, duplicates, FK references) and reports issues.
5. Database Generation — hands the validated schema to the `IntelligentDatabaseGenerator` which runs the full multi-table generation pipeline described above.

Response: same shape as `/generate-db`.

Notes on NL mode:
- The LLM's correctness is crucial: malformed JSON or ambiguous hints can require manual inspection or tweaking of prompts.
- The pipeline includes robust JSON-cleaning and repair heuristics to reduce parse failures.

## Agent Reference (backend internals)

This section documents the agents and their responsibilities. Each agent is implemented as a small class that calls the LLM and returns structured data.

### PrimaryKeyDetectionAgent (`PrimaryKeyDetectionAgent`)
- Purpose: Ensure each table has a clear primary key. Preferred name is table-specific, e.g., `department_id` for `departments`.
- Behavior: Scans fields for `id` variants, asks the LLM if an existing field is a suitable PK. If none, inserts a new auto-generated integer PK at position 0 of `fields` and marks `_auto_generated`.

### ForeignKeyDetectionAgent (`ForeignKeyDetectionAgent`)
- Purpose: Detect existing FK relationships by scanning fields and comparing to other tables' primary keys.
- Behavior: For each table, builds a prompt describing other tables and their fields; LLM returns a list of detected foreign keys with `field`, `references_table` and `references_field` which the generator converts into `field["references"]` entries.

### SchemaEnhancementAgent (`SchemaEnhancementAgent`)
- Purpose: When the FK detection step finds relationships conceptually but no FK fields exist, this agent recommends new FK fields to add (naming conventions like `<table>_id`).

### RelationshipInferenceAgent (`RelationshipInferenceAgent`)
- Purpose: Given a table's schema and FK info, produce short human-readable business rules used as generation hints (e.g., "Generate diverse job titles...", "Salary by department should vary...").

### DataValidationAgent (`DataValidationAgent`)
- Purpose: Ensure the generated data meets PK uniqueness, FK referential integrity, type constraints and business rules. Returns a structured report with `overall_valid`, `errors`, and `warnings`.

### TestDataGenerator (`TestDataGenerator` in `data_generator.py`)
- Purpose: Build LLM prompt for a single table and parse the returned JSON array into records.
- Key behaviors:
  - Includes parent table context (sample rows and available key values) in the prompt to help the LLM generate coherent FK values.
  - Implements a `_clean_json_response` function and a repair pass to handle typical LLM output issues (e.g., stray `null`, Python `True`/`None`, unmatched quotes) before `json.loads`.

### Natural Language Agents (in `nl_db_generator.py`)
- `TextParserAgent`: Extracts structured schema information from plain text.
- `SchemaDesignerAgent`: Produces realistic fields for a table.
- `RelationshipDetectorAgent`: Detects where to add FK fields.
- `SchemaValidatorAgent`: Light validation of the schema before generation.
- `NaturalLanguageDatabaseGenerator`: Orchestrates the above and calls `IntelligentDatabaseGenerator`.

## Important Implementation Notes & Recent Fixes

We made several defensive changes to improve stability when LLM outputs are inconsistent:

- Topological sort: `_topo_sort_tables` now uses Kahn's algorithm, detects cycles and returns a best-effort generation order while logging involved tables. This avoids crashing on mutual FK suggestions; cycles are reported for inspection.
## Test Data Generator — short & focused README

This repository generates realistic test data for single tables and multi-table databases using a small multi-agent pipeline and a local LLM (Ollama).

This cleaned README keeps only the essential information: quick start, key endpoints, natural-language mode summary, troubleshooting, and running tips.

---

## Quick start

Prerequisites
- Python 3.9+ (project includes `myenv` with Python 3.13)
- Node.js 16+ (optional — for frontend)
- Ollama installed and a local model (e.g., `llama3:latest`)

Start backend (from repo root):

```bash
source myenv/bin/activate
python -m uvicorn main:app --reload --port 8001
```

Start frontend (optional):

```bash
cd test-data-frontend
npm install
npm start
```

Health check: GET http://127.0.0.1:8001/health

---

## Core files
- `main.py` — FastAPI endpoints (/generate, /generate-db, /generate-from-text)
- `data_generator.py` — single-table LLM-based generator and JSON repair heuristics
- `intelligent_db_generator.py` — multi-table orchestration (PK/FK, topo-sort, injection, validation)
- `nl_db_generator.py` — natural-language pipeline (text → schema → generation)

---

## Key endpoints (summary)

POST /generate
- Single-table generation.
- Request: `schema_fields`, `num_records`, `correct_num_records`, `wrong_num_records`.
- Response: `{ data: [...], count: N }`.

POST /generate-db
- Multi-table generation with FK handling.
- Request: top-level `db_schema` with `tables` (name, fields, record counts).
- Response: generated tables, counts, generation order, and validation report.

POST /generate-from-text
- Natural Language Mode: send free text describing the DB; pipeline parses the schema and runs full generation.

---

## Natural Language Mode (short)

Flow: TextParserAgent → SchemaDesignerAgent → RelationshipDetectorAgent → SchemaValidatorAgent → IntelligentDatabaseGenerator.

Notes:
- The NL pipeline attempts to parse user text into a full schema and generate data.
- The backend includes JSON-cleaning and a repair pass to handle common LLM formatting issues.

---

## Quick troubleshooting

- LLM returns invalid JSON: check server logs for the raw LLM response and the cleaned JSON; consider lowering temperature and tightening prompts.
- Circular dependency between tables: the generator uses Kahn's algorithm and will log cycles; fix schema or add a join table.
- Parent table has no data: inspect LLM output for the parent; ensure its config is correct.

---

## Developer notes

- FK injection now avoids overwriting table PKs.
- Topological sort is cycle-tolerant and logs involved tables.
- JSON repair heuristics are in `data_generator.py` — add unit tests for them if you change logic.

---

If you'd like, I can now:
1. Run quick import checks for `main.py`, `data_generator.py`, and `intelligent_db_generator.py` (I can run Python imports in the venv).  
2. Add minimal unit tests for JSON-cleaning and FK-injection.  
3. Make the README even shorter or add an "explain" section that prints intermediate NL parsing results.

Tell me which of these to run next.

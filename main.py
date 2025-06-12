from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from qa_chain_async import ask_irda_question_long
from suggest_agent import generate_suggestions
import logging
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware

# ✅ Set root_path to "/api" since app is deployed under /api
app = FastAPI(root_path="/api", title="IRDA QA Agent")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
app.mount("/data", StaticFiles(directory=DATA_DIR), name="data")

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Configure CORS
origins = [
    "https://salesportal.watchyourhealth.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Request/Response models
class QueryRequest(BaseModel):
    question: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]

class SuggestRequest(BaseModel):
    answer: str

# Main question answering endpoint
@app.post("/ask", response_model=QueryResponse)
async def ask_question(req: QueryRequest):
    try:
       # Directly await the async QA coroutine—no asyncio.run()
        result = await ask_irda_question_long(req.session_id, req.question)
        return result
    except Exception as e:
        logging.exception("❌ Exception in /ask endpoint")
        # propagate a clean 500 with the error message
        raise HTTPException(status_code=500, detail=f"Internal Error: {e}")

# Suggest follow-up questions
@app.post("/suggest")
async def suggest_questions(request: SuggestRequest):
    try:
        suggestions = generate_suggestions(request.answer)
        return {"suggestions": suggestions}
    except Exception as e:
        logging.exception("❌ Exception in /suggest endpoint")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")

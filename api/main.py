import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from engine.pipeline import pipeline
import uuid

app = FastAPI()

SESSION_STORE: Dict[str, Dict[str, Any]] = {}


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    stage: str
    confidence_score: float
    questions: Optional[list] = None
    final_output: Optional[dict] = None


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):

    try:
        # 🔥 VALIDATION
        if not req.message or len(req.message) > 500:
            raise HTTPException(status_code=400, detail="Invalid message")

        # 🔥 SESSION CREATE
        session_id = req.session_id or str(uuid.uuid4())

        state = SESSION_STORE.get(session_id, {
            "history": [],
            "scores": {},
            "asked_questions": [],
            "ask_count": 0,
            "current_focus": None
        })

        state["history"].append(req.message)

        result, updated_state = pipeline(req.message, state)

        SESSION_STORE[session_id] = updated_state

        return {
            "session_id": session_id,
            "stage": result.get("stage", "questions"),
            "confidence_score": result.get("confidence_score", 0.0),
            "questions": result.get("questions"),
            "final_output": result.get("final_output")
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
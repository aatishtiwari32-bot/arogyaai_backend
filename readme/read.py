'''
Overview

This is a rule-based backend system for a health assistant that analyzes user symptoms and provides possible health-related guidance.
It processes user input, detects keywords, identifies possible problems (skin or mental), and returns either follow-up questions or a final structured response.

System Flow

User Input → Preprocess → Analyze → Prioritize → Decision → Output

Preprocess: cleans and normalizes text
Analyze: matches keywords with database
Prioritize: selects top problems
Pipeline: decides whether to ask questions or return final output
Project Structure
project/
│
├── main.py
│
├── engine/
│   ├── pipeline.py
│   ├── filter.py
│   ├── analyzer.py
│   └── prioritizer.py
│
├── database/
│   ├── skin.py
│   └── mental.py
API Endpoint
POST /chat
Request
{
    "session_id": "abc123",
    "message": "I have acne and stress"
}
Response
If more details are needed
{
    "stage": "questions",
    "confidence_score": 0,
    "questions": [
    "Tell me more about your problem."
    ],
    "final_output": null
}
Final Output
{
    "stage": "final",
    "confidence_score": 72.5,
    "final_output": {
    "problem_1": {
        "category": "skin",
        "name": "acne",
        "dos": [...],
        "donts": [...],
        "medicines": [...],
        "home_remedies": [...]
    }
    }
}
Core Logic
Keywords are extracted from user input
Matched against predefined databases
Score is calculated based on keyword match ratio
Top problems are selected using prioritization
If insufficient data → system asks questions
After 2 attempts → system forces final output
Database Structure

Each problem follows this format:

{
    "problem_name": {
    "keywords": [],
    "dos": [],
    "donts": [],
    "medicines": [],
    "homeremedies": [],
    "related_questions": []
    }
}
Key Features
Rule-based decision system
Supports multiple problems
Session-based interaction
Controlled question loop
Structured output for frontend
Limitations
No real AI or machine learning
No synonym understanding
No contextual language processing
Keyword-based matching only
No learning from user responses
Setup

Install dependencies:

pip install fastapi uvicorn nltk

Download NLTK data:

import nltk
nltk.download('punkt')

Run server:

uvicorn main:app --reload
Future Improvements
Answer-based confidence updates
Better NLP (synonyms, phrases)
Improved scoring system
AI/ML integration
Multi-problem refinement
Note

This is a rule-based MVP system designed as a foundation.
It can be extended into a more advanced intelligent system with further improvements.
'''

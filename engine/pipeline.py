from database.skin import skin_db
from database.mental import mental_db
from engine.filter import preprocess
from engine.analyzer import analyze
from engine.prioritizer import prioritize

from database.part import part_db 
def pipeline(text, state=None):

    # ---- safety ----
    if state is None:
        state = {}

    tokens = preprocess(text)

    
    skin_results = analyze(tokens, skin_db)
    mental_results = analyze(tokens, mental_db)

    # ---- match strength ----
    skin_matches = sum(len(v["matched_keywords"]) for v in skin_results.values())
    mental_matches = sum(len(v["matched_keywords"]) for v in mental_results.values())

    ask_count = state.get("ask_count", 0)

    # ======================
    # QUESTION PHASE
    # ======================
    if (skin_matches <= 1 and mental_matches <= 1):

        if ask_count < 2:
            state["ask_count"] = ask_count + 1

            if ask_count == 0:
                questions = [
                    "Tell me more about your problem.",
                    "Since when are you facing this issue?",
                    "Where exactly is it happening?"
                ]
            else:
                questions = [
                    "Please be more specific.",
                    "Are you feeling pain, itching, stress or discomfort?",
                    "Is it getting worse or stable?"
                ]

            return {
                "stage": "questions",
                "confidence_score": 0.0,
                "questions": questions,
                "final_output": None
            }, state

    # ======================
    # FINAL PHASE
    # ======================
    top_list = prioritize(skin_results, mental_results)

    if not top_list:
        return {
            "stage": "final",
            "confidence_score": 0.0,
            "questions": None,
            "final_output": {
                "status": "fail",
                "message": "Unable to determine clearly. Please consult a doctor.",
                "data": None
            }
        }, state

    final_output = {}
    scores = []

    for idx, item in enumerate(top_list, start=1):

        category = item["category"]
        problem = item["problem"]
        score = item["score"]

        db = skin_db if category == "skin" else mental_db
        problem_data = db.get(problem, {})

        final_output[f"problem_{idx}"] = {
            "category": category,
            "name": problem,
            "score": round(score, 3),
            "dos": problem_data.get("dos", []),
            "dont_s": problem_data.get("dont_s", []),
            "medicines": problem_data.get("medicines", []),
            "home_remedies": problem_data.get("home_remedies", [])
        }

        scores.append(score)

    confidence_score = round(sum(scores) / len(scores) * 100, 2) if scores else 0.0

    # reset state after final
    state["ask_count"] = 0

    return {
        "stage": "final",
        "confidence_score": confidence_score,
        "questions": None,
        "final_output": {
            "status": "success",
            "message": None,
            "data": final_output
        }
    }, state
from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.harmonal import harmonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db
from engine.filter import preprocess
from engine.analyzer import analyze
from engine.prioritizer import prioritize

def pipeline(text, state=None):

    # ---- safety ----
    if state is None:
        state = {}

    tokens = preprocess(text)

    
    skin_results = analyze(tokens, skin_db)
    mental_results = analyze(tokens, mental_db)
    harmonal_results = analyze(tokens, harmonal_db)
    blood_results = analyze(tokens, blood_db)
    bones_results = analyze(tokens, bones_db)
    joints_results = analyze(tokens, joints_db)
    digestion_results = analyze(tokens, digestion_db)
    lungs_results = analyze(tokens, lungs_db)
    
    skin_matches = sum(len(v["matched_keywords"]) for v in skin_results.values())
    mental_matches = sum(len(v["matched_keywords"]) for v in mental_results.values())
    harmonal_matches = sum(len(v["matched_keywords"]) for v in harmonal_results.values())
    blood_matches = sum(len(v["matched_keywords"]) for v in blood_results.values()) 
    bones_matches = sum(len(v["matched_keywords"]) for v in bones_results.values())
    joints_matches = sum(len(v["matched_keywords"]) for v in joints_results.values()) 
    digestion_matches = sum(len(v["matched_keywords"]) for v in digestion_results.values())
    lungs_matches = sum(len(v["matched_keywords"]) for v in lungs_results.values()) 
    
    ask_count = state.get("ask_count", 0)

    if (skin_matches <= 1 and mental_matches <= 1 and harmonal_matches <=1 and blood_matches <=1 and  bones_matches <=1 and joints_matches <=1 and digestion_matches <= 1 and lungs_matches <=1):

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

    top_list = prioritize(skin_results, mental_results, harmonal_results, blood_results, bones_results, joints_results, digestion_results, lungs_results )

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


        if category == "skin":
            db = skin_db
        elif category == "mental":
            db = mental_db
        elif category == "harmonal":
            db = harmonal_db
        elif category == "blood":
            db = blood_db            
        problem_data = db.get(problem, {})

        final_output[f"problem_{idx}"] = {
            "category": category,
            "name": problem,
            "score": round(score, 3),
            "matched_keywords": item.get("matched_keywords", []),
            "dos": problem_data.get("dos", []),
            "dont_s": problem_data.get("dont_s", []),
            "medicines": problem_data.get("medicines", []),
            "home_remedies": problem_data.get("home_remedies", []),
            "app_one_liner": problem_data.get("app_one_liner", ""),
            "deep_dive": problem_data.get("deep_dive", {})
        }

        scores.append(score)

    confidence_score = round(scores[0] * 100, 2)
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
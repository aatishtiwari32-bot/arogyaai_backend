from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.hormonal import hormonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db

first_reply = [
    "1", "a",
    "first", "pehela",
    "top", "primary"
]
second_reply = [
    "2", "b",
    "second", "dusra",
    "doosra", "middle",
    "between"
]
third_reply = [
    "3", "c",
    "third", "teesra",
    "last", "bottom"
]
def get_db(category):
    if category == "skin":
        return skin_db
    elif category == "blood":
        return blood_db
    elif category == "mental":
        return mental_db
    elif category == "hormonal":
        return hormonal_db
    elif category == "bones":
        return bones_db
    elif category == "joints":
        return joints_db
    elif category == "digestion":
        return digestion_db
    elif category == "lungs":
        return lungs_db
    return {}
def generate_clarification(top_list):

    if len(top_list) < 3:
        return None

    score1 = top_list[0]["score"]
    score2 = top_list[1]["score"]
    score3 = top_list[2]["score"]

    diff12 = abs(score1 - score2)
    diff13 = abs(score1 - score3)
    diff23 = abs(score2 - score3)

    if (
        diff12 > 10 or
        diff13 > 10 or
        diff23 > 10
    ):
        return None

    clarification = []

    for index, item in enumerate(top_list[:3]):

        category = item["category"]
        problem = item["problem"]

        db = get_db(category)

        problem_data = db.get(problem, {})

        symptoms = problem_data.get(
            "keywords",
            []
        )[:3]

        clarification.append({

            "index": index + 1,

            "category": category,

            "problem": problem,

            "score": item["score"],

            "symptoms": symptoms

        })

    return {

        "clarification_required": True,

        "problems": clarification

    }
def process_reply(
        user_reply,
        clarification_data
):
    user_reply = (
        user_reply
        .lower()
        .strip()
    )
    selected = None

    if user_reply in first_reply:
        selected = 0
    elif user_reply in second_reply:
        selected = 1
    elif user_reply in third_reply:
        selected = 2
    if selected is None:
        return None
    problems = clarification_data["problems"]
    if selected >= len(problems):
        return None
    chosen_problem = problems[selected]
    current_score = chosen_problem["score"]
    if current_score < 60:
        chosen_problem["score"] = 80
    else:
        chosen_problem["score"] += 20
    problems.sort(
        key=lambda x: x["score"],
        reverse=True
    )
    return problems
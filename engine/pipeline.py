from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.hormonal import hormonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db

from engine.reply_engine import generate_clarification, process_reply
from engine.filter import preprocess
from engine.prioritizer import prioritize
from engine.category_routing import routing


def pipeline(text, state=None):

    if state is None:
        state = {}

    if state.get("clarification_mode"):

        clarified_result = process_reply(
            text,
            state["clarification_data"]
        )

        if clarified_result:

            state["clarification_mode"] = False
            state["clarification_complete"] = True

            return {

                "stage": "clarification_resolved",

                "confidence_score":
                    clarified_result[0]["score"],

                "questions": None,

                "clarification_data": None,

                "final_output": {

                    "status": "success",

                    "message":
                        "Clarification completed",

                    "data":
                        clarified_result
                }

            }, state
    tokens = preprocess(text)
    results = routing(tokens)

    skin_results = results["skin"]
    mental_results = results["mental"]
    blood_results = results["blood"]
    hormonal_results = results["hormonal"]
    bones_results = results["bones"]
    joints_results = results["joints"]
    digestion_results = results["digestion"]
    lungs_results = results["lungs"]

    skin_matches = sum(
        len(v["matched_keywords"])
        for v in skin_results.values()
    )

    mental_matches = sum(
        len(v["matched_keywords"])
        for v in mental_results.values()
    )

    hormonal_matches = sum(
        len(v["matched_keywords"])
        for v in hormonal_results.values()
    )

    blood_matches = sum(
        len(v["matched_keywords"])
        for v in blood_results.values()
    )

    bones_matches = sum(
        len(v["matched_keywords"])
        for v in bones_results.values()
    )

    joints_matches = sum(
        len(v["matched_keywords"])
        for v in joints_results.values()
    )

    digestion_matches = sum(
        len(v["matched_keywords"])
        for v in digestion_results.values()
    )

    lungs_matches = sum(
        len(v["matched_keywords"])
        for v in lungs_results.values()
    )

    ask_count = state.get(
        "ask_count",
        0
    )

    if (
        skin_matches <= 1 and
        mental_matches <= 1 and
        hormonal_matches <= 1 and
        blood_matches <= 1 and
        bones_matches <= 1 and
        joints_matches <= 1 and
        digestion_matches <= 1 and
        lungs_matches <= 1
    ):

        if ask_count < 2:

            state["ask_count"] = (
                ask_count + 1
            )

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

                "clarification_data": None,

                "final_output": None

            }, state

    top_list = prioritize(
        skin_results,
        mental_results,
        hormonal_results,
        blood_results,
        bones_results,
        joints_results,
        digestion_results,
        lungs_results
    )

    if not top_list:

        return {

            "stage": "final",

            "confidence_score": 0.0,

            "questions": None,

            "clarification_data": None,

            "final_output": {

                "status": "fail",

                "message":
                "Unable to determine clearly. Please consult a doctor.",

                "data": None
            }

        }, state
    clarification_data = generate_clarification(top_list)
    if clarification_data:
        state["clarification_mode"] = True
        state["clarification_data"] = (
            clarification_data
        )
        return {
            "stage": "clarification",
            "confidence_score": 0.0,
            "questions": None,
            "clarification_data":
            clarification_data,
            "final_output": None
        }, state
    final_output = {}
    scores = []
    for idx, item in enumerate(
        top_list,
        start=1
    ):
        category = item["category"]
        problem = item["problem"]
        score = item["score"]
        if category == "skin":
            db = skin_db
        elif category == "mental":
            db = mental_db
        elif category == "hormonal":
            db = hormonal_db
        elif category == "blood":
            db = blood_db
        elif category == "bones":
            db = bones_db
        elif category == "joints":
            db = joints_db
        elif category == "digestion":
            db = digestion_db
        elif category == "lungs":
            db = lungs_db
        else:
            db = {}
        problem_data = db.get(
            problem,
            {}
        )
        final_output[
            f"problem_{idx}"
        ] = {
            "category":
            category,
            "name":
            problem,
            "score":
            round(score, 2),
            "matched_keywords":
            item.get(
                "matched_keywords",
                []
            ),
            "dos":
            problem_data.get(
                "dos",
                []
            ),
            "dont_s":
            problem_data.get(
                "dont_s",
                []
            ),
            "medicines":
            problem_data.get(
                "medicines",
                []
            ),
            "home_remedies":
            problem_data.get(
                "home_remedies",
                []
            ),
            "app_one_liner":
            problem_data.get(
                "app_one_liner",
                ""
            ),
            "deep_dive":
            problem_data.get(
                "deep_dive",
                {}
            )
        }
        scores.append(score)
    confidence_score = round(
        scores[0],
        2
    )
    state["ask_count"] = 0
    return {
        "stage": "final",
        "confidence_score":
        confidence_score,
        "questions": None,
        "clarification_data": None,
        "final_output": {
            "status": "success",
            "message": None,
            "data": final_output
        }
    }, state
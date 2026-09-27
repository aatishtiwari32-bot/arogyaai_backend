from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.hormonal import hormonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db

from engine.reply_engine import (
    generate_clarification,
    process_reply
)

from engine.filter import preprocess
from engine.prioritizer import prioritize
from engine.category_routing import routing


# ============================================================
# DATABASE MAP
# ============================================================

DATABASES = {
    "skin": skin_db,
    "mental": mental_db,
    "hormonal": hormonal_db,
    "blood": blood_db,
    "bones": bones_db,
    "joints": joints_db,
    "digestion": digestion_db,
    "lungs": lungs_db
}


# ============================================================
# DEFAULT STATE
# ============================================================

DEFAULT_STATE = {
    "history": [],
    "scores": {},
    "asked_questions": [],
    "ask_count": 0,
    "current_focus": None,

    # Clarification state
    "clarification_mode": False,
    "clarification_data": None,
    "clarification_answer": None,
    "clarification_complete": False
}


# ============================================================
# INITIALIZE STATE
# ============================================================

def initialize_state(state):
    """
    Ensure that all required session fields exist.
    """

    if not isinstance(state, dict):
        state = {}

    for key, default_value in DEFAULT_STATE.items():

        if key not in state:

            if isinstance(
                default_value,
                list
            ):
                state[key] = []

            elif isinstance(
                default_value,
                dict
            ):
                state[key] = {}

            else:
                state[key] = default_value

    return state


# ============================================================
# BUILD ONE PROBLEM OUTPUT
# ============================================================

def build_problem_output(item):
    """
    Convert one prioritized problem into the final response
    structure using the corresponding database entry.
    """

    if not isinstance(
        item,
        dict
    ):
        return None

    category = item.get(
        "category"
    )

    problem = item.get(
        "problem"
    )

    if not category or not problem:
        return None

    score = item.get(
        "score",
        0.0
    )

    matched_keywords = item.get(
        "matched_keywords",
        []
    )

    db = DATABASES.get(
        category,
        {}
    )

    problem_data = db.get(
        problem,
        {}
    )

    if not isinstance(
        problem_data,
        dict
    ):
        problem_data = {}

    return {
        "category": category,

        "name": problem,

        # For the prototype this represents the engine's
        # evidence score, NOT medical probability.
        "score": round(
            float(score),
            4
        ),

        "matched_keywords": matched_keywords,

        "dos": problem_data.get(
            "dos",
            []
        ),

        "dont_s": problem_data.get(
            "dont_s",
            []
        ),

        "medicines": problem_data.get(
            "medicines",
            []
        ),

        "home_remedies": problem_data.get(
            "home_remedies",
            []
        ),

        "app_one_liner": problem_data.get(
            "app_one_liner",
            ""
        ),

        "deep_dive": problem_data.get(
            "deep_dive",
            {}
        )
    }


# ============================================================
# BUILD FINAL OUTPUT
# ============================================================

def build_final_output(top_list):
    """
    Convert a list of prioritized problems into:

        problem_1
        problem_2
        problem_3
    """

    final_output = {}

    if not isinstance(
        top_list,
        list
    ):
        return final_output

    for index, item in enumerate(
        top_list,
        start=1
    ):

        problem_output = build_problem_output(
            item
        )

        if problem_output is None:
            continue

        final_output[
            f"problem_{index}"
        ] = problem_output

    return final_output


# ============================================================
# QUESTION GENERATOR
# ============================================================

def generate_questions(ask_count):
    """
    Generate follow-up questions based on the current
    conversation stage.
    """

    if ask_count == 0:

        return [
            "Tell me more about your problem.",
            "Since when are you facing this issue?",
            "Where exactly is it happening?"
        ]

    return [
        "Please be more specific.",
        "Are you feeling pain, itching, stress or discomfort?",
        "Is the problem getting worse or staying the same?"
    ]


# ============================================================
# QUESTION RESPONSE
# ============================================================

def question_response(
    state,
    ask_count
):
    """
    Prepare a question-stage response and update session state.
    """

    questions = generate_questions(
        ask_count
    )

    state["ask_count"] = (
        ask_count + 1
    )

    state["asked_questions"].extend(
        questions
    )

    return {
        "stage": "questions",

        "confidence_score": 0.0,

        "questions": questions,

        "clarification_data": None,

        "final_output": None

    }, state


# ============================================================
# FAILURE RESPONSE
# ============================================================

def failure_response(state):
    """
    Prepare a clean failure response and reset temporary
    diagnosis/clarification state.
    """

    state["ask_count"] = 0

    state["clarification_mode"] = False

    state["clarification_data"] = None

    state["clarification_answer"] = None

    state["clarification_complete"] = False

    state["current_focus"] = None

    return {
        "stage": "final",

        "confidence_score": 0.0,

        "questions": None,

        "clarification_data": None,

        "final_output": {
            "status": "fail",

            "message":
                "Unable to determine clearly. Please provide more information or consult a doctor.",

            "data": None
        }

    }, state


# ============================================================
# MAIN PIPELINE
# ============================================================

def pipeline(
    text,
    state=None
):
    """
    Main Arogya AI prototype pipeline.

    Complete flow:

        User message
            ↓
        Session state
            ↓
        Clarification check
            ↓
        Conversation history
            ↓
        Preprocessing
            ↓
        Category routing
            ↓
        Problem analysis
            ↓
        Weighted evidence
            ↓
        Prioritization
            ↓
        Clarification OR final result
    """

    # ========================================================
    # INITIALIZE STATE
    # ========================================================

    state = initialize_state(
        state
    )

    # ========================================================
    # VALIDATE TEXT
    # ========================================================

    if not isinstance(
        text,
        str
    ):
        return failure_response(
            state
        )

    text = text.strip()

    if not text:

        return {
            "stage": "questions",

            "confidence_score": 0.0,

            "questions": [
                "Please describe your problem."
            ],

            "clarification_data": None,

            "final_output": None

        }, state

    # ========================================================
    # CLARIFICATION MODE
    # ========================================================
    #
    # If the previous response asked the user to choose
    # between multiple candidate problems, the new message
    # is interpreted as that choice.
    # ========================================================

    if state.get(
        "clarification_mode",
        False
    ):

        clarification_data = state.get(
            "clarification_data"
        )

        clarified_result = process_reply(
            text,
            clarification_data
        )

        # ----------------------------------------------------
        # INVALID CLARIFICATION RESPONSE
        #
        # Example:
        #
        # "hello"
        # "4"
        # "I don't know"
        #
        # Keep clarification mode active.
        # ----------------------------------------------------

        if not clarified_result:

            return {
                "stage": "clarification",

                "confidence_score": 0.0,

                "questions": None,

                "clarification_data":
                    clarification_data,

                "final_output": None

            }, state

        # ====================================================
        # VALID CLARIFICATION RESPONSE
        # ====================================================

        state["clarification_mode"] = False

        state["clarification_complete"] = True

        state["clarification_answer"] = text

        state["ask_count"] = 0

        selected_problem = clarified_result[
            0
        ]

        # ----------------------------------------------------
        # The selected problem keeps its original evidence
        # score.
        #
        # No artificial +20.
        # No artificial 80.
        # ----------------------------------------------------

        confidence_score = round(
            float(
                selected_problem.get(
                    "score",
                    0.0
                )
            ),
            4
        )

        # ----------------------------------------------------
        # Only the selected problem is returned as final
        # output after clarification.
        # ----------------------------------------------------

        final_output = build_final_output(
            [
                selected_problem
            ]
        )

        if not final_output:

            return failure_response(
                state
            )

        state["current_focus"] = {
            "category":
                selected_problem.get(
                    "category"
                ),

            "problem":
                selected_problem.get(
                    "problem"
                )
        }

        return {
            "stage": "clarification_resolved",

            "confidence_score":
                confidence_score,

            "questions": None,

            "clarification_data": None,

            "final_output": {
                "status": "success",

                "message":
                    "Clarification completed",

                "data": final_output
            }

        }, state

    # ========================================================
    # ADD MESSAGE TO HISTORY
    # ========================================================
    #
    # api/main.py already appends the message before calling
    # pipeline().
    #
    # This fallback allows pipeline() to also work when called
    # directly in Python tests.
    # ========================================================

    history = state.get(
        "history",
        []
    )

    if not isinstance(
        history,
        list
    ):
        history = []

        state["history"] = history

    if not history:

        history.append(
            text
        )

    elif history[-1] != text:

        history.append(
            text
        )

    # ========================================================
    # BUILD COMPLETE CONVERSATION TEXT
    # ========================================================
    #
    # Every previous user message is combined.
    #
    # Example:
    #
    # Turn 1:
    # "red rash on foot"
    #
    # Turn 2:
    # "for three weeks"
    #
    # Turn 3:
    # "very itchy"
    #
    # Analyzer receives all useful information together.
    # ========================================================

    analysis_text = " ".join(
        str(message)
        for message in history
        if isinstance(
            message,
            str
        )
    )

    # ========================================================
    # PREPROCESS
    # ========================================================

    tokens = preprocess(
        analysis_text
    )

    # ========================================================
    # EMPTY TOKEN RESULT
    # ========================================================

    if not tokens:

        ask_count = state.get(
            "ask_count",
            0
        )

        if ask_count < 2:

            return question_response(
                state,
                ask_count
            )

        return failure_response(
            state
        )

    # ========================================================
    # CATEGORY ROUTING
    # ========================================================

    results = routing(
        tokens
    )

    if not isinstance(
        results,
        dict
    ):

        return failure_response(
            state
        )

    # ========================================================
    # GET CATEGORY RESULTS
    # ========================================================

    skin_results = results.get(
        "skin",
        {}
    )

    mental_results = results.get(
        "mental",
        {}
    )

    blood_results = results.get(
        "blood",
        {}
    )

    hormonal_results = results.get(
        "hormonal",
        {}
    )

    bones_results = results.get(
        "bones",
        {}
    )

    joints_results = results.get(
        "joints",
        {}
    )

    digestion_results = results.get(
        "digestion",
        {}
    )

    lungs_results = results.get(
        "lungs",
        {}
    )

    # ========================================================
    # SAVE BASIC ENGINE INFORMATION
    # ========================================================
    #
    # These are useful for debugging the prototype.
    #
    # IMPORTANT:
    # These are NOT used anymore to decide whether a result
    # is valid. Analyzer/weight_engine handle candidate
    # strength.
    # ========================================================

    state["scores"] = {

        "skin":
            len(skin_results),

        "mental":
            len(mental_results),

        "blood":
            len(blood_results),

        "hormonal":
            len(hormonal_results),

        "bones":
            len(bones_results),

        "joints":
            len(joints_results),

        "digestion":
            len(digestion_results),

        "lungs":
            len(lungs_results)
    }

    # ========================================================
    # PRIORITIZATION
    # ========================================================
    #
    # IMPORTANT:
    #
    # Analyzer does not sort.
    #
    # Prioritizer receives all valid candidates and orders
    # them according to weighted evidence.
    # ========================================================

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

    # ========================================================
    # NO VALID CANDIDATE
    # ========================================================

    if not top_list:

        ask_count = state.get(
            "ask_count",
            0
        )

        if ask_count < 2:

            return question_response(
                state,
                ask_count
            )

        return failure_response(
            state
        )

    # ========================================================
    # CURRENT FOCUS
    # ========================================================

    state["current_focus"] = {

        "category":
            top_list[0].get(
                "category"
            ),

        "problem":
            top_list[0].get(
                "problem"
            )
    }

    # ========================================================
    # CLARIFICATION CHECK
    # ========================================================

    clarification_data = (
        generate_clarification(
            top_list
        )
    )

    # --------------------------------------------------------
    # Multiple close candidates
    # --------------------------------------------------------

    if clarification_data:

        state["clarification_mode"] = True

        state["clarification_data"] = (
            clarification_data
        )

        state["clarification_answer"] = None

        state["clarification_complete"] = False

        state["ask_count"] = 0

        return {
            "stage": "clarification",

            "confidence_score": 0.0,

            "questions": None,

            "clarification_data":
                clarification_data,

            "final_output": None

        }, state

    # ========================================================
    # BUILD FINAL OUTPUT
    # ========================================================
    final_output = build_final_output(
        top_list
    )
    # Safety check
    if not final_output:
        return failure_response(
            state
        )
    # FINAL CONFIDENCE / EVIDENCE SCORE
    #
    # For skin:
    #     weighted evidence score
    #
    # For other categories:
    #     current analyzer score
    #
    # This remains a prototype evidence score and should not
    # be interpreted as a medical probability.
    top_score = top_list[0].get(
        "score",
        0.0
    )
    try:
        confidence_score = round(
            float(top_score),
            4
        )
    except (
        TypeError,
        ValueError
    ):
        confidence_score = 0.0
    # RESET TEMPORARY STATE
    state["ask_count"] = 0
    state["clarification_mode"] = False
    state["clarification_data"] = None
    state["clarification_answer"] = None
    state["clarification_complete"] = False
    # FINAL RESPONSE
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
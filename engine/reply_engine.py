import re
from copy import deepcopy
from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.hormonal import hormonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db
# DATABASE LOOKUP
def get_db(category):
    """
    Return the database associated with a category.
    """
    databases = {
        "skin": skin_db,
        "blood": blood_db,
        "mental": mental_db,
        "hormonal": hormonal_db,
        "bones": bones_db,
        "joints": joints_db,
        "digestion": digestion_db,
        "lungs": lungs_db
    }
    return databases.get(
        category,
        {}
    )
# USER OPTION PARSING
FIRST_OPTION_WORDS = {
    "1",
    "first",
    "primary",
    "one"
}
SECOND_OPTION_WORDS = {
    "2",
    "second",
    "two"
}
THIRD_OPTION_WORDS = {
    "3",
    "third",
    "three"
}
def parse_selection(user_reply):
    """
    Convert a user's clarification reply into an option index.
    Supported examples:
        "1"
        "first"
        "option 1"
        "number 1"
        "second"
        "2"
        "third"
        "3"
    Returns
    -------
    int | None
        0 -> first option
        1 -> second option
        2 -> third option
        None -> invalid selection
    """
    if not isinstance(user_reply, str):
        return None
    reply = user_reply.lower().strip()
    if not reply:
        return None
    # Exact word matches
    if reply in FIRST_OPTION_WORDS:
        return 0
    if reply in SECOND_OPTION_WORDS:
        return 1
    if reply in THIRD_OPTION_WORDS:
        return 2
    # Extract option number from common phrases.
    #
    # Examples:
    #
    # "option 1"
    # "option one"
    # "number 2"
    # "choice 3"
    # "select 1"
    number_match = re.search(
        r"\b(?:option|number|choice|select)\s*(1|2|3)\b",
        reply
    )
    if number_match:
        number = int(
            number_match.group(1)
        )
        return number - 1
    return None
# GENERATE CLARIFICATION
def generate_clarification(top_list):
    """
    Decide whether clarification is required.
    Clarification is shown only when there are at least
    three candidate problems and their scores are close.
    Current prototype rule:
        maximum score difference <= 10
    Returns
    -------
    dict | None
    """
    if not isinstance(top_list, list):
        return None
    if len(top_list) < 3:
        return None
    # Only top 3 candidates participate in clarification.
    candidates = top_list[:3]
    scores = []
    for item in candidates:
        if not isinstance(item, dict):
            return None
        score = item.get(
            "score",
            0
        )
        if not isinstance(score, (int, float)):
            return None
        scores.append(
            float(score)
        )
    # If the candidates are not close enough,
    # don't ask clarification.
    score_difference = (
        max(scores) - min(scores)
    )
    if score_difference > 10:
        return None
    # BUILD CLARIFICATION DATA
    problems = []
    for index, item in enumerate(candidates):
        category = item.get(
            "category"
        )
        problem = item.get(
            "problem"
        )
        score = item.get(
            "score",
            0
        )
        db = get_db(
            category
        )
        problem_data = db.get(
            problem,
            {}
        )
        # Prefer the symptoms actually matched by the analyzer.
        # If unavailable, fall back to first 3 DB keywords.
        symptoms = item.get(
            "matched_keywords",
            []
        )
        if not symptoms:
            symptoms = problem_data.get(
                "keywords",
                []
            )[:3]
        problems.append({
            "index": index + 1,
            "category": category,
            "problem": problem,
            "score": round(
                float(score),
                2
            ),
            "symptoms": symptoms,
            "selected": False
        })
    return {
        "clarification_required": True,
        "problems": problems
    }
# PROCESS USER REPLY
def process_reply(
    user_reply,
    clarification_data
):
    """
    Process a user's clarification choice.
    IMPORTANT:
    The original diagnostic score is NOT modified.
    The selected problem is simply marked as selected and
    moved to the top of the result.
    Returns
    -------
    list | None
    """
    if not isinstance(
        clarification_data,
        dict
    ):
        return None
    problems = clarification_data.get(
        "problems",
        []
    )
    if not isinstance(problems, list):
        return None
    if not problems:
        return None
    # Parse user's selection
    selected_index = parse_selection(
        user_reply
    )
    if selected_index is None:
        return None
    # Validate selected index
    if (
        selected_index < 0
        or selected_index >= len(problems)
    ):
        return None
    # IMPORTANT:
    #
    # Work on a deep copy.
    # Don't mutate state[clarification_data].
    updated_problems = deepcopy(
        problems
    )
    # Mark all as not selected
    for problem in updated_problems:
        problem["selected"] = False
    # Mark chosen problem
    updated_problems[
        selected_index
    ]["selected"] = True
    # Move selected problem to the top.
    # Score stays EXACTLY the same.
    selected_problem = updated_problems.pop(
        selected_index
    )
    updated_problems.insert(
        0,
        selected_problem
    )
    # Return chosen problem first.
    return updated_problems
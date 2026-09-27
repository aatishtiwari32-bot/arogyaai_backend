from engine.analyzer import analyze, normalize_keyword
from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.hormonal import hormonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db
from database.identification import (
    blood_identifiers,
    bones_identifiers,
    digestion_identifiers,
    hormonal_identifiers,
    mental_identifiers,
    joints_identifiers,
    respiratory_identifiers,
    skin_identifiers
)
# ============================================================
# CATEGORY CONFIGURATION
# ============================================================
CATEGORY_CONFIG = {
    "blood": {
        "identifiers": blood_identifiers,
        "db": blood_db,
    },
    "bones": {
        "identifiers": bones_identifiers,
        "db": bones_db,
    },
    "digestion": {
        "identifiers": digestion_identifiers,
        "db": digestion_db,
    },
    "hormonal": {
        "identifiers": hormonal_identifiers,
        "db": hormonal_db,
    },
    "mental": {
        "identifiers": mental_identifiers,
        "db": mental_db,
    },
    "joints": {
        "identifiers": joints_identifiers,
        "db": joints_db,
    },
    "lungs": {
        "identifiers": respiratory_identifiers,
        "db": lungs_db,
    },
    "skin": {
        "identifiers": skin_identifiers,
        "db": skin_db,
    },
}
# PREPARE IDENTIFIERS
def prepare_identifiers(identifier_list):
    """
    Converts raw identifiers into normalized/stemmed
    token tuples.
    Example:
        "joint pain"
        ->
        ("joint", "pain")
        "joints"
        ->
        ("joint",)
    """
    prepared = []
    if not isinstance(identifier_list, list):
        return prepared
    seen = set()
    for identifier in identifier_list:
        normalized = normalize_keyword(
            identifier
        )
        if not normalized:
            continue
        if normalized in seen:
            continue
        seen.add(normalized)
        prepared.append(normalized)
    return prepared
# Prepare once when the application starts.
PREPARED_IDENTIFIERS = {
    category: prepare_identifiers(
        config["identifiers"]
    )
    for category, config in CATEGORY_CONFIG.items()
}
# CATEGORY SCORE
def calculate_category_score(tokens, identifiers):
    """
    Calculates how strongly a category is indicated by
    the user's normalized tokens.
    A complete identifier phrase counts as one match.
    Example:
        tokens:
            ["joint", "pain"]
        identifier:
            ("joint", "pain")
        => 1 category match
    """
    if not tokens:
        return 0
    token_set = set(tokens)
    score = 0
    for identifier_tokens in identifiers:
        identifier_set = set(
            identifier_tokens
        )
        if not identifier_set:
            continue
        # Full phrase match
        if identifier_set.issubset(token_set):
            score += 1
    return score
# MAIN ROUTER
def routing(tokens):
    """
    Routes user input to the most relevant medical categories.
    Flow:
        tokens
          ↓
        category scoring
          ↓
        top relevant categories
          ↓
        analyze only those databases
    """
    # Empty input
    if not tokens:
        return {
            category: {}
            for category in CATEGORY_CONFIG
        }
    # CALCULATE CATEGORY SCORES
    category_scores = {}
    for category, identifiers in PREPARED_IDENTIFIERS.items():
        category_scores[category] = (
            calculate_category_score(
                tokens,
                identifiers
            )
        )
    # SORT CATEGORIES
    sorted_categories = sorted(
        category_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )
    # SELECT TOP CATEGORIES
    top_categories = [
        category
        for category, score in sorted_categories
        if score > 0
    ][:3]
    # CREATE EMPTY RESULT STRUCTURE
    results = {
        category: {}
        for category in CATEGORY_CONFIG
    }
    # FALLBACK
    #
    # If the router has no category signal,
    # analyze every database.
    if not top_categories:
        for category, config in CATEGORY_CONFIG.items():
            results[category] = analyze(
                tokens,
                config["db"],
                category=category
            )
        return results
    # ANALYZE ONLY ROUTED CATEGORIES
    for category in top_categories:
        config = CATEGORY_CONFIG[
            category
        ]
        results[category] = analyze(
            tokens,
            config["db"]
        )
    return results
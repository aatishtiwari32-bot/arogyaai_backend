import re

from nltk.stem import PorterStemmer

from engine.weight_engine import (
    WEIGHT_DB,
    MIN_WEIGHT,
    calculate_total_weight
)


# ============================================================
# STEMMER
# ============================================================

ps = PorterStemmer()


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "i",
    "have",
    "has",
    "had",

    "is",
    "am",
    "are",
    "was",
    "were",

    "the",
    "a",
    "an",

    "and",
    "or",

    "to",
    "of",
    "in",
    "on",

    "for",
    "with",

    "my",
    "me",

    "he",
    "she",

    "there",

    "because",
    "that",

    "having",
    "while",

    "around",
    "experiencing",
    "during"
}


# ============================================================
# MATCHING CONFIGURATION
# ============================================================

# Minimum percentage of tokens from a database keyword
# that must match the user's input.
#
# Examples:
#
# 2-token keyword:
#     2 / 2 = 100%
#
# 3-token keyword:
#     3 / 3 = 100%
#
# 4-token keyword:
#     3 / 4 = 75%
#
COVERAGE_THRESHOLD = 0.75


# ============================================================
# FUZZY MATCHING CONFIGURATION
# ============================================================

# Maximum edit distance allowed.
#
# Short words:
#     maximum 1 edit
#
# Longer words:
#     maximum 2 edits
#
MAX_SHORT_WORD_DISTANCE = 1
MAX_LONG_WORD_DISTANCE = 2


# ============================================================
# NORMALIZE KEYWORD
# ============================================================

def normalize_keyword(
    keyword: str
):
    """
    Normalize a database keyword/phrase.

    Example:

        "Painful pimples"

    becomes approximately:

        ("pain", "pimpl")
    """

    if not isinstance(
        keyword,
        str
    ):
        return ()

    keyword = (
        keyword
        .lower()
        .strip()
    )

    if not keyword:
        return ()

    words = re.findall(
        r"[a-zA-Z]+",
        keyword
    )

    normalized = []

    for word in words:

        if word in STOP_WORDS:
            continue

        normalized.append(
            ps.stem(word)
        )

    return tuple(
        normalized
    )


# ============================================================
# EDIT DISTANCE
# ============================================================

def edit_distance(
    word1: str,
    word2: str
):
    """
    Calculate Levenshtein edit distance.

    Operations:

        insertion
        deletion
        substitution
    """

    if word1 == word2:
        return 0

    if not word1:
        return len(word2)

    if not word2:
        return len(word1)

    previous_row = list(
        range(
            len(word2) + 1
        )
    )

    for i, char1 in enumerate(
        word1,
        start=1
    ):

        current_row = [
            i
        ]

        for j, char2 in enumerate(
            word2,
            start=1
        ):

            insertion = (
                current_row[j - 1]
                + 1
            )

            deletion = (
                previous_row[j]
                + 1
            )

            substitution = (
                previous_row[j - 1]
                +
                (
                    char1 != char2
                )
            )

            current_row.append(
                min(
                    insertion,
                    deletion,
                    substitution
                )
            )

        previous_row = current_row

    return previous_row[-1]


# ============================================================
# TOKEN MATCHING
# ============================================================

def token_matches(
    keyword_token,
    user_token
):
    """
    Safely compare one normalized keyword token
    with one normalized user token.

    Matching rules:

        1. Exact match
        2. Controlled fuzzy match

    Fuzzy matching is intentionally conservative.

    Examples:

        foot  <-> fooot      ✅
        itch  <-> itcch      ✅

        hair  <-> itch       ❌
        pain  <-> foot       ❌
    """

    if not keyword_token:
        return False

    if not user_token:
        return False

    # ========================================================
    # EXACT MATCH
    # ========================================================

    if keyword_token == user_token:
        return True

    # ========================================================
    # LENGTH CHECK
    # ========================================================

    keyword_length = len(
        keyword_token
    )

    user_length = len(
        user_token
    )

    length_difference = abs(
        keyword_length
        -
        user_length
    )

    # Too different in size.
    if length_difference > 2:
        return False

    # ========================================================
    # FIRST CHARACTER GUARD
    # ========================================================
    #
    # This is important for avoiding nonsense fuzzy matches.
    #
    # Example:
    #
    # hair
    # itch
    #
    # same length but completely different words.
    #
    # We don't want those to match.
    # ========================================================

    if (
        keyword_token[0]
        !=
        user_token[0]
    ):
        return False

    # ========================================================
    # EDIT DISTANCE
    # ========================================================

    distance = edit_distance(
        keyword_token,
        user_token
    )

    # ========================================================
    # SHORT WORDS
    # ========================================================

    if (
        keyword_length <= 5
        and user_length <= 5
    ):

        return (
            distance
            <= MAX_SHORT_WORD_DISTANCE
        )

    # ========================================================
    # LONG WORDS
    # ========================================================

    return (
        distance
        <= MAX_LONG_WORD_DISTANCE
    )


# ============================================================
# MATCH KEYWORD TOKENS
# ============================================================

def match_keyword_tokens(
    keyword_tokens,
    user_tokens
):
    """
    Match a keyword's tokens against user tokens.

    Word order DOES NOT matter.

    Example:

        Database keyword:

            ("itch", "foot")

        User:

            ["foot", "itch"]

        Result:

            2 / 2 = 100%

    Every user token can be used only once.
    """

    if not keyword_tokens:
        return 0

    if not user_tokens:
        return 0

    used_user_indices = set()

    matched_count = 0

    # ========================================================
    # MATCH EVERY KEYWORD TOKEN
    # ========================================================

    for keyword_token in keyword_tokens:

        found_match = False

        for index, user_token in enumerate(
            user_tokens
        ):

            # User token already used for another keyword token.
            if index in used_user_indices:
                continue

            if token_matches(
                keyword_token,
                user_token
            ):

                used_user_indices.add(
                    index
                )

                matched_count += 1

                found_match = True

                break

        if found_match:
            continue

    return matched_count


# ============================================================
# KEYWORD COVERAGE
# ============================================================

def keyword_coverage(
    keyword_tokens,
    user_tokens
):
    """
    Calculate the percentage of a database keyword
    that was matched in the user message.

    Returns:

        0.0 -> no match
        0.5 -> half matched
        0.75 -> 75% matched
        1.0 -> complete match
    """

    if not keyword_tokens:
        return 0.0

    matched_count = match_keyword_tokens(
        keyword_tokens,
        user_tokens
    )

    return (
        matched_count
        /
        len(keyword_tokens)
    )


# ============================================================
# LEGACY SCORE
# ============================================================

def calculate_legacy_score(
    matched_count,
    total_keywords
):
    """
    Calculate the original percentage score for categories
    that do not yet use the weighted engine.

    Example:

        2 matched out of 10
        -> 20.0
    """

    if total_keywords <= 0:
        return 0.0

    return round(
        (
            matched_count
            /
            total_keywords
        )
        * 100,
        2
    )


# ============================================================
# ANALYZER
# ============================================================

def analyze(
    tokens: list,
    db: dict,
    partial_match: bool = False,
    category: str | None = None
):
    """
    Analyze a medical database against user tokens.

    Responsibilities:

        1. Normalize database keywords.
        2. Match keywords against user tokens.
        3. Ignore keyword word order.
        4. Handle small spelling mistakes.
        5. Apply 75% token coverage.
        6. Calculate weighted evidence when available.

    This function DOES NOT sort results.

    Sorting is handled by prioritizer.py.
    """

    # ========================================================
    # INPUT VALIDATION
    # ========================================================

    if not isinstance(
        tokens,
        list
    ):
        return {}

    if not isinstance(
        db,
        dict
    ):
        return {}

    # ========================================================
    # NORMALIZE USER TOKENS
    # ========================================================

    user_tokens = []

    for token in tokens:

        if not isinstance(
            token,
            str
        ):
            continue

        token = token.strip().lower()

        if not token:
            continue

        user_tokens.append(
            ps.stem(token)
        )

    if not user_tokens:
        return {}

    # ========================================================
    # RESULT CONTAINER
    # ========================================================

    results = {}

    # ========================================================
    # PROCESS EVERY PROBLEM
    # ========================================================

    for problem, data in db.items():

        if not isinstance(
            data,
            dict
        ):
            continue

        keywords = data.get(
            "keywords",
            []
        )

        if not isinstance(
            keywords,
            list
        ):
            continue

        matched_keywords = []

        seen_keyword_signatures = set()

        # ====================================================
        # PROCESS EVERY DATABASE KEYWORD
        # ====================================================

        for keyword in keywords:

            if not isinstance(
                keyword,
                str
            ):
                continue

            keyword = keyword.strip()

            if not keyword:
                continue

            # ------------------------------------------------
            # Normalize keyword.
            # ------------------------------------------------

            keyword_tokens = normalize_keyword(
                keyword
            )

            if not keyword_tokens:
                continue

            # ------------------------------------------------
            # Remove duplicate normalized keywords.
            #
            # Example:
            #
            # "pimple"
            # "pimples"
            #
            # If both normalize to the same representation,
            # they count as ONE keyword concept.
            # ------------------------------------------------

            if keyword_tokens in seen_keyword_signatures:
                continue

            seen_keyword_signatures.add(
                keyword_tokens
            )

            # ------------------------------------------------
            # Calculate coverage.
            # ------------------------------------------------

            coverage = keyword_coverage(
                keyword_tokens,
                user_tokens
            )

            # ------------------------------------------------
            # Current prototype:
            #
            # 75% keyword-token coverage required.
            #
            # partial_match is kept in the function signature
            # for compatibility with the previous engine.
            # ------------------------------------------------

            threshold = COVERAGE_THRESHOLD

            if coverage >= threshold:

                matched_keywords.append(
                    keyword.lower()
                )

        # ====================================================
        # NOTHING MATCHED
        # ====================================================

        if not matched_keywords:
            continue

        # ====================================================
        # WEIGHTED CATEGORY
        # ====================================================

        if category in WEIGHT_DB:

            total_weight = (
                calculate_total_weight(
                    category,
                    problem,
                    matched_keywords
                )
            )

            # ------------------------------------------------
            # Weak weighted evidence is discarded.
            # ------------------------------------------------

            if total_weight < MIN_WEIGHT:
                continue

            results[problem] = {

                # Main ranking value.
                "score": round(
                    total_weight,
                    4
                ),

                # Explicit weighted score.
                "weighted_score": round(
                    total_weight,
                    4
                ),

                # Same value kept explicitly for debugging.
                "total_weight": round(
                    total_weight,
                    4
                ),

                # Actual evidence that triggered this result.
                "matched_keywords":
                    matched_keywords,

                # Useful debugging information.
                "matched_keyword_count":
                    len(
                        matched_keywords
                    ),

                "total_keywords":
                    len(
                        seen_keyword_signatures
                    )
            }

        # ====================================================
        # NON-WEIGHTED CATEGORY
        # ====================================================
        #
        # Other categories can continue using the existing
        # scoring model until their own weight engines exist.
        # ====================================================

        else:

            if len(matched_keywords) < 2:
                continue

            raw_score = calculate_legacy_score(
                len(matched_keywords),
                len(seen_keyword_signatures)
            )

            results[problem] = {

                "score":
                    raw_score,

                "weighted_score":
                    None,

                "total_weight":
                    None,

                "matched_keywords":
                    matched_keywords,

                "matched_keyword_count":
                    len(
                        matched_keywords
                    ),
                "total_keywords":
                    len(
                        seen_keyword_signatures
                    )
            }
    # IMPORTANT:
    #
    # DO NOT SORT HERE.
    #
    # prioritizer.py owns ranking.
    return results
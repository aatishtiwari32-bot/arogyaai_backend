import re
from difflib import SequenceMatcher

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

# Minimum percentage of keyword tokens that must match.
#
# Example:
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


# Minimum fuzzy similarity for a token-level typo match.
FUZZY_THRESHOLD = 0.75


# For very short words fuzzy matching can create false matches.
# Therefore fuzzy matching is disabled for words shorter than 4
# characters.
MIN_FUZZY_LENGTH = 4


# ============================================================
# NORMALIZE KEYWORD
# ============================================================

def normalize_keyword(
    keyword: str
):
    """
    Normalize one database keyword/phrase.

    Example:

        "Painful pimples"
            ->
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
# TOKEN SIMILARITY
# ============================================================

def token_matches(
    keyword_token,
    user_token
):
    """
    Determine whether one keyword token matches one user token.

    Matching levels:

        1. Exact normalized match
        2. Safe prefix match
        3. Fuzzy similarity match

    Examples:

        itch  -> itch      ✅
        itch  -> itchingg  → handled conservatively
        foot  -> foot      ✅
    """

    if not keyword_token or not user_token:
        return False

    # --------------------------------------------------------
    # Exact match
    # --------------------------------------------------------

    if keyword_token == user_token:
        return True

    # --------------------------------------------------------
    # Fuzzy matching should NOT be used for tiny words.
    #
    # Otherwise:
    #
    #     "flu"
    #     "fly"
    #
    # could become a false match.
    # --------------------------------------------------------

    if (
        len(keyword_token) < MIN_FUZZY_LENGTH
        or len(user_token) < MIN_FUZZY_LENGTH
    ):
        return False

    # --------------------------------------------------------
    # Safe prefix check
    #
    # Useful for cases where stemming does not completely
    # remove a spelling variation.
    #
    # Example:
    #
    #     itch
    #     itchign
    #
    # --------------------------------------------------------

    shorter = min(
        keyword_token,
        user_token,
        key=len
    )

    longer = max(
        keyword_token,
        user_token,
        key=len
    )

    length_difference = (
        len(longer)
        -
        len(shorter)
    )

    if (
        len(shorter) >= 4
        and length_difference <= 3
        and longer.startswith(shorter)
    ):
        return True

    # --------------------------------------------------------
    # Sequence similarity
    # --------------------------------------------------------

    similarity = SequenceMatcher(
        None,
        keyword_token,
        user_token
    ).ratio()

    return (
        similarity >= FUZZY_THRESHOLD
    )


# ============================================================
# MATCH KEYWORD TOKENS
# ============================================================

def match_keyword_tokens(
    keyword_tokens,
    user_tokens
):
    """
    Match keyword tokens against user tokens.

    IMPORTANT:

        Order does NOT matter.

    Example:

        keyword:
            ("itch", "foot")

        user:
            ["foot", "itch"]

        result:
            2 / 2 = 100%

    Each user token can only be used once.
    """

    if not keyword_tokens:
        return 0

    if not user_tokens:
        return 0

    used_user_indices = set()

    matched_count = 0

    # --------------------------------------------------------
    # Match every keyword token against an unused user token.
    # --------------------------------------------------------

    for keyword_token in keyword_tokens:

        found_match = False

        for index, user_token in enumerate(
            user_tokens
        ):

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

        if not found_match:
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
    Calculate what percentage of a keyword's tokens
    matched the user's input.
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
    Legacy percentage score for categories whose weighted
    engine is not implemented yet.
    """

    if total_keywords <= 0:
        return 0.0

    return round(
        (
            matched_count
            /
            total_keywords
        ) * 100,
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
    Analyze one medical database against the user's tokens.

    Responsibilities:

        1. Match database keywords.
        2. Support spelling variations.
        3. Ignore keyword word order.
        4. Calculate weighted evidence when available.

    Ranking is NOT performed here.

    Ranking belongs to prioritizer.py.
    """

    # ========================================================
    # VALIDATE INPUT
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
    # CLEAN USER TOKENS
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
        # PROCESS EVERY KEYWORD
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
            keyword_tokens = normalize_keyword(
                keyword
            )
            if not keyword_tokens:
                continue
            # Avoid duplicate normalized keywords.
            #
            # Example:
            #
            # pimple
            # pimples
            #
            # may normalize to the same representation.
            if keyword_tokens in seen_keyword_signatures:
                continue
            seen_keyword_signatures.add(
                keyword_tokens
            )
            # Calculate token coverage.
            coverage = keyword_coverage(
                keyword_tokens,
                user_tokens
            )
            # MATCH DECISION
            #
            # Default = 75%
            #
            # partial_match exists for compatibility with the
            # old engine. We do not lower the threshold because
            # the current prototype is explicitly using 75%.
            if coverage >= COVERAGE_THRESHOLD:
                matched_keywords.append(
                    keyword.lower()
                )
        # NO KEYWORD MATCH
        if not matched_keywords:
            continue
        # WEIGHTED CATEGORY
        if category in WEIGHT_DB:
            total_weight = (
                calculate_total_weight(
                    category,
                    problem,
                    matched_keywords
                )
            )
            # Weak weighted evidence is discarded.
            if total_weight < MIN_WEIGHT:
                continue
            results[problem] = {
                # Main ranking value.
                "score": round(
                    total_weight,
                    4
                ),
                "weighted_score": round(
                    total_weight,
                    4
                ),
                "total_weight": round(
                    total_weight,
                    4
                ),
                "matched_keywords":
                    matched_keywords,
                "matched_keyword_count":
                    len(matched_keywords),
                "total_keywords":
                    len(
                        seen_keyword_signatures
                    )
            }
        # ====================================================
        # NON-WEIGHTED CATEGORY
        # ====================================================
        else:
            # Keep existing behaviour for categories which
            # don't yet have their own weight engine.
            if len(matched_keywords) < 2:
                continue
            raw_score = calculate_legacy_score(
                len(matched_keywords),
                len(seen_keyword_signatures)
            )
            results[problem] = {
                "score": raw_score,
                "weighted_score": None,
                "total_weight": None,
                "matched_keywords":
                    matched_keywords,
                "matched_keyword_count":
                    len(matched_keywords),
                "total_keywords":
                    len(
                        seen_keyword_signatures
                    )
            }
    # IMPORTANT
    #
    # DO NOT SORT HERE.
    #
    # prioritizer.py is responsible for ranking.
    return results
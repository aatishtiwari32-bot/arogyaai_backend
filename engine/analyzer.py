import re

from nltk.stem import PorterStemmer

from engine.weight_engine import (
    WEIGHT_DB,
    MIN_WEIGHT,
    calculate_total_weight
)


ps = PorterStemmer()


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "i", "have", "has", "had",
    "is", "am", "are", "was", "were",
    "the", "a", "an",
    "and", "or",
    "to", "of", "in", "on",
    "for", "with",
    "my", "me",
    "he", "she", "there",
    "because", "that",
    "having", "while",
    "around", "experiencing",
    "during"
}


# ============================================================
# NORMALIZE KEYWORD
# ============================================================

def normalize_keyword(
    keyword: str
):
    """
    Normalize one database keyword.

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

    keyword = keyword.lower().strip()

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
# CALCULATE LEGACY SCORE
# ============================================================

def calculate_legacy_score(
    matched_count: int,
    total_keywords: int
):
    """
    Used only by categories that do not yet have a
    weighted database.

    Skin uses weighted evidence instead.
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
    Match user tokens against a problem database.

    Responsibilities of this function:

        1. Find matching keywords.
        2. Calculate weighted evidence when available.
        3. Return candidate information.

    This function DOES NOT rank/sort the problems.
    Ranking is handled by prioritizer.py.
    """

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

    # --------------------------------------------------------
    # User token set
    # --------------------------------------------------------

    token_set = {
        ps.stem(
            str(token).lower()
        )
        for token in tokens
        if str(token).strip()
    }

    if not token_set:
        return {}

    results = {}

    # ========================================================
    # LOOP THROUGH PROBLEMS
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

        normalized_keywords = []

        seen_signatures = set()

        # ----------------------------------------------------
        # Normalize and deduplicate database keywords.
        # ----------------------------------------------------

        for keyword in keywords:

            normalized = normalize_keyword(
                keyword
            )

            if not normalized:
                continue

            if normalized in seen_signatures:
                continue

            seen_signatures.add(
                normalized
            )

            normalized_keywords.append(
                (
                    keyword.lower().strip(),
                    normalized
                )
            )

        if not normalized_keywords:
            continue

        # ====================================================
        # MATCH KEYWORDS
        # ====================================================

        matched_keywords = []

        for original_keyword, keyword_tokens in normalized_keywords:

            keyword_set = set(
                keyword_tokens
            )

            if not keyword_set:
                continue

            matched_words = len(
                keyword_set.intersection(
                    token_set
                )
            )

            coverage = (
                matched_words
                /
                len(keyword_set)
            )

            # ------------------------------------------------
            # Exact/full matching
            # ------------------------------------------------

            if not partial_match:

                if coverage == 1.0:

                    matched_keywords.append(
                        original_keyword
                    )

            # ------------------------------------------------
            # Partial matching
            # ------------------------------------------------

            else:

                if coverage >= 0.8:

                    matched_keywords.append(
                        original_keyword
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
            # Ignore weak evidence.
            #
            # This replaces:
            #
            #     len(matched_keywords) < 2
            #
            # for weighted categories.
            # ------------------------------------------------

            if total_weight < MIN_WEIGHT:
                continue

            results[problem] = {

                # Primary ranking value
                "score": total_weight,

                # Explicit name for clarity
                "weighted_score": total_weight,

                "total_weight": total_weight,

                "matched_keywords":
                    matched_keywords,

                "matched_keyword_count":
                    len(matched_keywords),

                "total_keywords":
                    len(normalized_keywords)
            }

        # ====================================================
        # NON-WEIGHTED CATEGORY
        # ====================================================

        else:

            # Keep old behaviour for categories whose
            # weighting system has not been built yet.

            if len(matched_keywords) < 2:
                continue
            raw_score = calculate_legacy_score(
                len(matched_keywords),
                len(normalized_keywords)
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
                    len(normalized_keywords)
            }
    # ========================================================
    # IMPORTANT:
    #
    # NO SORTING HERE.
    #
    # prioritizer.py owns ranking.
    # ========================================================
    return results
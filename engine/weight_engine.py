import math
from database.skin import skin_db
from engine.filter import preprocess
# WEIGHT CONFIGURATION
# Minimum weighted evidence required for a skin problem
# to remain a candidate.
#
# This is a prototype threshold, not a medical threshold.
MIN_WEIGHT = 4.0
# KEYWORD NORMALIZATION
def normalize_keyword(keyword: str) -> tuple:
    """
    Normalize a database keyword using the same preprocessing
    pipeline used by the application.
    Example:
        "itching foot"
            ->
        ("itch", "foot")
    """
    if not isinstance(keyword, str):
        return ()
    keyword = keyword.strip()
    if not keyword:
        return ()
    tokens = preprocess(keyword)
    if not tokens:
        return ()
    return tuple(tokens)
# BUILD PROBLEM TOKEN SETS
def build_problem_token_sets(db: dict):
    """
    For every problem, build a set containing all normalized
    tokens appearing anywhere in its keywords.
    Example:
        athlete_foot
        ->
        {
            "itch",
            "foot",
            "fung",
            "toe",
            "crack",
            ...
        }
    """
    problem_token_sets = {}
    for problem, data in db.items():
        if not isinstance(data, dict):
            continue
        keywords = data.get(
            "keywords",
            []
        )
        token_set = set()
        if isinstance(keywords, list):
            for keyword in keywords:
                normalized = normalize_keyword(
                    keyword
                )
                for token in normalized:
                    token_set.add(token)
        problem_token_sets[problem] = token_set
    return problem_token_sets
# TOKEN DOCUMENT FREQUENCY
def build_token_document_frequency(
    problem_token_sets: dict
):
    """
    Count how many different problems contain a token.
    Example:
        "itch"
            -> many problems
        "toe"
            -> fewer problems
    Therefore a rare token carries more information.
    """
    document_frequency = {}
    for token_set in problem_token_sets.values():
        for token in token_set:
            document_frequency[token] = (
                document_frequency.get(
                    token,
                    0
                ) + 1
            )
    return document_frequency
# IDF / TOKEN SPECIFICITY
def calculate_idf(
    document_frequency: int,
    total_documents: int
):
    """
    IDF-style specificity score.
    Common token:
        lower value
    Rare token:
        higher value
    """
    return math.log(
        (total_documents + 1)
        /
        (document_frequency + 1)
    ) + 1
# KEYWORD CO-OCCURRENCE FREQUENCY
def calculate_keyword_cooccurrence(
    keyword_tokens: tuple,
    problem_token_sets: dict
):
    """
    Count how many problems contain ALL tokens from a keyword.
    Example:
        keyword = ("itch", "foot")
    We count problems where both "itch" AND "foot"
    occur somewhere in that problem's keyword collection.
    This is more useful than simply counting words.
    """
    if not keyword_tokens:
        return 0
    keyword_token_set = set(
        keyword_tokens
    )
    count = 0
    for problem_tokens in problem_token_sets.values():
        if keyword_token_set.issubset(
            problem_tokens
        ):
            count += 1
    return count
# KEYWORD WEIGHT
def calculate_keyword_weight(
    keyword_tokens: tuple,
    token_idf: dict,
    cooccurrence_df: int,
    total_documents: int
):
    """
    Calculate the information weight of one keyword.
    IMPORTANT:
    This is NOT based simply on number of words.
    It considers:
        1. Rarity of its tokens
        2. Rarity of the token combination
    The combination component makes a phrase such as:
        "itching foot"
    stronger than a generic token such as:
        "itching"
    when the combination is much less common.
    """
    if not keyword_tokens:
        return 0.0
    # IDF values of tokens inside the keyword.
    token_weights = [
        token_idf.get(
            token,
            1.0
        )
        for token in keyword_tokens
    ]
    if not token_weights:
        return 0.0
    max_token_idf = max(
        token_weights
    )
    average_token_idf = (
        sum(token_weights)
        /
        len(token_weights)
    )
    # How rare is the complete token combination?
    phrase_idf = calculate_idf(
        cooccurrence_df,
        total_documents
    )
    # Final keyword weight
    #
    # 60% -> combination specificity
    # 40% -> token specificity
    #
    # Max token receives extra importance so one distinctive
    # term is not drowned by generic words.
    weight = (
        0.60 * phrase_idf
        +
        0.25 * max_token_idf
        +
        0.15 * average_token_idf
    )
    return round(
        weight,
        4
    )
# BUILD SKIN WEIGHT DATABASE
def build_skin_weight_db():
    """
    Automatically generate weights for every keyword in
    te existing skin_db.
    No manual duplication of the disease database is required.
    Output structure:
        {
            "acne": {
                "pimple":  ...,
                "acne":    ...,
                "face bumps": ...
            },
            "athlete_foot": {
                "itching foot": ...,
                "fungus foot": ...,
                ...
            }
        }
    """
    total_documents = len(
        skin_db
    )
    if total_documents == 0:
        return {}
    # Step 1:
    # Build normalized token set for every problem.
    problem_token_sets = (
        build_problem_token_sets(
            skin_db
        )
    )
    # Step 2:
    # Calculate token document frequency.
    document_frequency = (
        build_token_document_frequency(
            problem_token_sets
        )
    )
    # Step 3:
    # Calculate IDF for every token.
    token_idf = {}
    for token, df in document_frequency.items():
        token_idf[token] = calculate_idf(
            df,
            total_documents
        )
    # Step 4:
    # Build final problem -> keyword -> weight structure.
    weight_db = {}
    for problem, data in skin_db.items():
        weight_db[problem] = {}
        if not isinstance(data, dict):
            continue
        keywords = data.get(
            "keywords",
            []
        )
        if not isinstance(keywords, list):
            continue
        seen_signatures = set()
        for keyword in keywords:
            if not isinstance(
                keyword,
                str
            ):
                continue
            keyword = keyword.strip()
            if not keyword:
                continue
            normalized_tokens = (
                normalize_keyword(
                    keyword
                )
            )
            if not normalized_tokens:
                continue
            signature = tuple(
                normalized_tokens
            )
            # Avoid duplicates such as:
            #
            # pimple
            # pimples
            #
            # when they normalize to the same form.
            if signature in seen_signatures:
                continue
            seen_signatures.add(
                signature
            )
            cooccurrence_df = (
                calculate_keyword_cooccurrence(
                    normalized_tokens,
                    problem_token_sets
                )
            )
            weight = calculate_keyword_weight(
                normalized_tokens,
                token_idf,
                cooccurrence_df,
                total_documents
            )
            weight_db[problem][
                keyword.lower()
            ] = weight
    return weight_db
# ============================================================
# GENERATED WEIGHT DATABASE
# ============================================================
# This is the category-wise structure you wanted.
WEIGHT_DB = {
    "skin": build_skin_weight_db()
}
# ============================================================
# GET KEYWORD WEIGHT
# ============================================================
def get_keyword_weight(
    category: str,
    problem: str,
    keyword: str
):
    """
    Return the weight of one matched keyword.
    """
    category_data = WEIGHT_DB.get(
        category,
        {}
    )
    problem_data = category_data.get(
        problem,
        {}
    )
    if not isinstance(
        keyword,
        str
    ):
        return 0.0
    keyword = keyword.lower().strip()
    return round(
        float(
            problem_data.get(
                keyword,
                0.0
            )
        ),
        4
    )
# ============================================================
# CALCULATE TOTAL WEIGHT
# ============================================================
def calculate_total_weight(
    category: str,
    problem: str,
    matched_keywords: list
):
    """
    Calculate ONLY the total weight of keywords that
    analyzer.py actually matched.

    Unmatched keywords contribute ZERO.
    """
    if not isinstance(
        matched_keywords,
        list
    ):
        return 0.0
    total_weight = 0.0
    seen = set()
    for keyword in matched_keywords:
        if not isinstance(
            keyword,
            str
        ):
            continue
        keyword = keyword.lower().strip()
        if not keyword:
            continue
        # Avoid duplicate contribution.
        if keyword in seen:
            continue
        seen.add(
            keyword
        )
        total_weight += get_keyword_weight(
            category,
            problem,
            keyword
        )
    return round(
        total_weight,
        4
    )
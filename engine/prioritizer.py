def prioritize(
    skin_results: dict,
    mental_results: dict,
    hormonal_results: dict,
    blood_results: dict,
    bones_results: dict,
    joints_results: dict,
    digestion_results: dict,
    lungs_results: dict,
    top_k: int = 3
):
    """
    Combine candidate problems from all categories and rank them.
    For categories with weighted analysis:
        weighted_score -> primary ranking
    For categories without weighted analysis:
        score -> fallback ranking
    This function is responsible for ordering.
    Analyzer is not.
    """
    if top_k <= 0:
        return []
    all_results = {
        "skin": skin_results,
        "mental": mental_results,
        "hormonal": hormonal_results,
        "blood": blood_results,
        "bones": bones_results,
        "joints": joints_results,
        "digestion": digestion_results,
        "lungs": lungs_results
    }
    merged = []
    # COLLECT RESULTS
    for category, results in all_results.items():
        if not isinstance(
            results,
            dict
        ):
            continue
        for problem, data in results.items():
            if not isinstance(
                data,
                dict
            ):
                continue
            score = data.get(
                "score",
                0
            )
            weighted_score = data.get(
                "weighted_score"
            )
            # Weighted score is primary where available.
            if isinstance(
                weighted_score,
                (int, float)
            ):
                ranking_score = float(
                    weighted_score
                )
            else:
                ranking_score = float(
                    score
                )
            if ranking_score <= 0:
                continue
            merged.append({
                "category":
                    category,
                "problem":
                    problem,
                "score":
                    round(
                        ranking_score,
                        4
                    ),
                "weighted_score":
                    (
                        round(
                            float(weighted_score),
                            4
                        )
                        if isinstance(
                            weighted_score,
                            (int, float)
                        )
                        else None
                    ),
                "total_weight":
                    data.get(
                        "total_weight"
                    ),
                "matched_keywords":
                    data.get(
                        "matched_keywords",
                        []
                    )
            })
    # NO RESULTS
    if not merged:
        return []
    # SORT
    #
    # 1. Higher ranking evidence
    # 2. More matched keywords
    # 3. Alphabetical problem name
    #
    # Deterministic ordering.
    merged.sort(
        key=lambda item: (
            -item["score"],
            -len(
                item.get(
                    "matched_keywords",
                    []
                )
            ),
            item["problem"]
        )
    )
    # TOP K
    return merged[
        :top_k
    ]
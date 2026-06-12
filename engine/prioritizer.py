def prioritize(
        skin_results: dict,
        mental_results: dict,
        hormonal_results: dict,
        blood_results: dict,
        bones_results: dict,
        joints_results: dict,
        digestion_results: dict,
        lungs_results: dict,
        top_k: int = 3,
        min_score: float = 10.0
):

    merged = []

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

    for category, results in all_results.items():

        for problem, data in results.items():

            score = data.get("score", 0)

            if score < min_score:
                continue

            merged.append({
                "category": category,
                "problem": problem,
                "score": score,
                "matched_keywords":
                    data.get("matched_keywords", [])
            })

    if not merged:
        return []

    merged.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return merged[:top_k]
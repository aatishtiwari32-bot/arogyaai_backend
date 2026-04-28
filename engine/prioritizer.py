def prioritize(skin_results: dict,
            mental_results: dict,
            top_k: int = 3,
            min_score: float = 0.2):
    """
    Merges skin & mental results, filters by min_score,
    sorts by score (desc), and returns top_k problems.

    Output format (pipeline-compatible):
    [
    {"category": "skin", "problem": "acne", "score": 0.6},
    {"category": "mental", "problem": "stress", "score": 0.5},
    ...
    ]
    """

    merged = []

    # ---- merge skin ----
    for name, data in skin_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "skin",
                "problem": name,
                "score": score
            })

    # ---- merge mental ----
    for name, data in mental_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "mental",
                "problem": name,
                "score": score
            })

    # ---- no match case ----
    if not merged:
        return []

    # ---- sort by score (descending) ----
    merged.sort(key=lambda x: x["score"], reverse=True)

    # ---- optional: ensure diversity (at least 1 from each category if possible) ----
    skin_items = [item for item in merged if item["category"] == "skin"]
    mental_items = [item for item in merged if item["category"] == "mental"]

    diversified = []

    # pick top from each category first (if available)
    if skin_items:
        diversified.append(skin_items[0])
    if mental_items:
        diversified.append(mental_items[0])

    # fill remaining slots from merged (avoid duplicates)
    for item in merged:
        if item not in diversified:
            diversified.append(item)
        if len(diversified) >= top_k:
            break

    return diversified[:top_k]
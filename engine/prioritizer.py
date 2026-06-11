def prioritize(skin_results: dict,
            mental_results: dict,
            hormonal_results: dict,
            blood_results: dict,
            bones_results:dict,
            joints_results: dict,
            digestion_results: dict,
            lungs_results: dict,
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
    for name, data in skin_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "skin",
                "problem": name,
                "score": score
            })
    for name, data in mental_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "mental",
                "problem": name,
                "score": score
            })
    for name, data in hormonal_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "hormonal",
                "problem": name,
                "score": score
            })
    for name, data in blood_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "blood",
                "problem": name,
                "score": score
            })  
    for name, data in bones_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "bones",
                "problem": name,
                "score": score
            })
    for name, data in joints_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "joints",
                "problem": name,
                "score": score
            })
    for name, data in digestion_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "digestion",
                "problem": name,
                "score": score
            })  
    for name, data in lungs_results.items():
        score = data.get("score", 0.0)
        if score >= min_score:
            merged.append({
                "category": "lungs and respiratory",
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
    hormonal_items = [item for item in merged if item["category"] == "hormonal"]
    blood_items = [item for item in merged if item["category"] == "blood"]
    bones_items = [item for item in merged if item["category"] == "bones"]
    joints_items = [item for item in merged if item["category"] == "joints"]
    digestion_items = [item for item in merged if item["category"] == "digestion"]
    lungs_items = [item for item in merged if item["category"] == "lungs and respiratory"]
    
    diversified = []

    # pick top from each category first (if available)
    if skin_items:
        diversified.append(skin_items[0])
    if mental_items:
        diversified.append(mental_items[0])
    if hormonal_items:
        diversified.append(hormonal_items[0])
    if blood_items:
        diversified.append(blood_items[0])
    if bones_items:
        diversified.append(bones_items[0])
    if joints_items:
        diversified.append(joints_items[0])
    if digestion_items:
        diversified.append(digestion_items[0])
    if lungs_items:
        diversified.append(lungs_items[0])    
    # fill remaining slots from merged (avoid duplicates)
    for item in merged:
        if item not in diversified:
            diversified.append(item)
        if len(diversified) >= top_k:
            break

    return diversified[:top_k]
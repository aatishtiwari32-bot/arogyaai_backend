from nltk.stem import PorterStemmer

ps = PorterStemmer()

def analyze(tokens: list, db: dict):

    token_set = set(tokens)
    results = {}

    for problem, data in db.items():

        keywords = data.get("keywords", [])
        if not keywords:
            continue

        matched = []

        for kw in keywords:
            kw_clean = kw.lower().strip()
            kw_words = kw_clean.split()

            # stem keyword words
            kw_stems = [ps.stem(w) for w in kw_words]

            # count partial matches
            match_count = sum(1 for w in kw_stems if w in token_set)

            # 🔥 flexible match condition
            if match_count >= max(1, len(kw_stems) // 2):
                matched.append(kw_clean)

        if matched:
            score = len(matched)

            results[problem] = {
                "score": score,
                "matched_keywords": matched,
                "total_keywords": len(keywords)
            }

    return results
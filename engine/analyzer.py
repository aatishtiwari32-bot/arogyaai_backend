from nltk.stem import PorterStemmer

ps = PorterStemmer()

STOP_WORDS = {
    "i", "have", "is", "am", "are", "the", "a", "an",
    "and", "or", "to", "of", "in", "on", "for",
    "with", "my", "me", "he", "she", "there",
    "because", "that", "having", "while",
    "around", "experiencing", "during"
}
def analyze(tokens: list, db: dict, partial_match=False):
    token_set = set(tokens)
    temp_results = {}
    for problem, data in db.items():
        keywords = data.get("keywords", [])
        if not keywords:
            continue
        matched_keywords = []
        for kw in keywords:
            kw_clean = kw.lower().strip()
            # split keyword
            words = kw_clean.split()
            # remove stopwords
            words = [
                w for w in words
                if w not in STOP_WORDS
            ]
            # stem keyword words
            keyword_set = {
                ps.stem(w)
                for w in words
            }
            if not keyword_set:
                continue
            matched_words = len(
                keyword_set.intersection(token_set)
            )
            coverage = (
                matched_words
                / len(keyword_set)
            )
            # ---- first turn ----
            if not partial_match:
                if coverage == 1.0:
                    matched_keywords.append(
                        kw_clean
                    )
            # ---- second turn ----
            else:
                if coverage >= 0.8:
                    matched_keywords.append(
                        kw_clean
                    )
        # minimum 2 matched keywords
        if len(matched_keywords) < 2:
            continue
        total_keywords = len(keywords)
        score = round(
            (
                len(matched_keywords)
                / total_keywords
            ) * 100,
            2
        )
        temp_results[problem] = {
            "score": score,
            "matched_keywords":
                matched_keywords,
            "total_keywords":
                total_keywords
        }
    sorted_results = dict(
        sorted(
            temp_results.items(),
            key=lambda item:
                item[1]["score"],
            reverse=True
        )
    )
    return sorted_results
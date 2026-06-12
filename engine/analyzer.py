from nltk.stem import PorterStemmer

ps = PorterStemmer()

def analyze(tokens: list, db: dict):

    token_set = set(tokens)

    temp_results = {}

    for problem, data in db.items():

        keywords = data.get("keywords", [])

        if not keywords:
            continue

        matched_keywords = []

        for kw in keywords:

            kw_clean = kw.lower().strip()

            kw_words = kw_clean.split()

            kw_stems = [
                ps.stem(w)
                for w in kw_words
            ]

            match_count = sum(
                1
                for w in kw_stems
                if w in token_set
            )

            required_matches = max(
                1,
                len(kw_stems) // 2
            )

            if match_count >= required_matches:

                matched_keywords.append(
                    kw_clean
                )

        # at least 2 matched keywords
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
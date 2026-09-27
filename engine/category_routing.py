from engine.analyzer import analyze

from database.skin import skin_db
from database.blood import blood_db
from database.mental import mental_db
from database.hormonal import hormonal_db
from database.bones import bones_db
from database.joints import joints_db
from database.digestion import digestion_db
from database.respiratory import lungs_db

from database.identification import (
    blood_identifiers,
    bones_identifiers,
    digestion_identifiers,
    hormonal_identifiers,
    mental_identifiers,
    joints_identifiers,
    respiratory_identifiers,
    skin_identifiers
)


def routing(tokens):

    bl = 0
    bo = 0
    di = 0
    ho = 0
    me = 0
    jo = 0
    re = 0
    sk = 0

    for w in tokens:

        if w in blood_identifiers:
            bl += 1

        if w in bones_identifiers:
            bo += 1

        if w in digestion_identifiers:
            di += 1

        if w in hormonal_identifiers:
            ho += 1

        if w in mental_identifiers:
            me += 1

        if w in joints_identifiers:
            jo += 1

        if w in respiratory_identifiers:
            re += 1

        if w in skin_identifiers:
            sk += 1

    categories = {
        "blood": bl,
        "bones": bo,
        "digestion": di,
        "hormonal": ho,
        "mental": me,
        "joints": jo,
        "lungs": re,
        "skin": sk
    }

    sorted_categories = sorted(
        categories.items(),
        key=lambda x: x[1],
        reverse=True
    )

    results = {
        "skin": {},
        "mental": {},
        "blood": {},
        "hormonal": {},
        "bones": {},
        "joints": {},
        "digestion": {},
        "lungs": {}
    }

    # categories jinka score > 0 hai
    top_categories = [
        category
        for category, score in sorted_categories
        if score > 0
    ][:3]

    # fallback mode
    if not top_categories:

        results["blood"] = analyze(tokens, blood_db)
        results["bones"] = analyze(tokens, bones_db)
        results["digestion"] = analyze(tokens, digestion_db)
        results["hormonal"] = analyze(tokens, hormonal_db)
        results["mental"] = analyze(tokens, mental_db)
        results["joints"] = analyze(tokens, joints_db)
        results["lungs"] = analyze(tokens, lungs_db)
        results["skin"] = analyze(tokens, skin_db)

        return results

    # analyze only routed categories
    for category in top_categories:

        if category == "blood":
            results["blood"] = analyze(tokens, blood_db)

        elif category == "bones":
            results["bones"] = analyze(tokens, bones_db)

        elif category == "digestion":
            results["digestion"] = analyze(tokens, digestion_db)

        elif category == "hormonal":
            results["hormonal"] = analyze(tokens, hormonal_db)

        elif category == "mental":
            results["mental"] = analyze(tokens, mental_db)

        elif category == "joints":
            results["joints"] = analyze(tokens, joints_db)

        elif category == "lungs":
            results["lungs"] = analyze(tokens, lungs_db)

        elif category == "skin":
            results["skin"] = analyze(tokens, skin_db)

    return results
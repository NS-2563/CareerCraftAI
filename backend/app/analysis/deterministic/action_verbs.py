"""Action verb detection and analysis.

Deterministic — detects action verbs in resume descriptions.
Provides structured results for scoring and feedback.
"""
import re
from typing import Any, Dict, List


_ACTION_VERBS = {
    "achieved", "acquired", "adapted", "addressed", "administered", "advanced",
    "advised", "advocated", "allocated", "analyzed", "applied", "appointed",
    "architected", "assembled", "assessed", "assigned", "assisted", "attained",
    "audited", "authored", "automated",
    "bolstered", "boosted", "brought", "broadened", "built",
    "calculated", "catalyzed", "centralized", "chaired", "championed",
    "clarified", "classified", "coached", "collaborated", "combined",
    "communicated", "compared", "compiled", "completed", "composed",
    "computed", "conceived", "conceptualized", "concluded", "conducted",
    "configured", "confirmed", "connected", "consolidated", "constructed",
    "consulted", "continued", "contributed", "converted", "conveyed",
    "coordinated", "corrected", "correlated", "counseled", "created",
    "cultivated", "customized",
    "debriefed", "debugged", "decentralized", "decided", "decreased",
    "defined", "delegated", "delivered", "demonstrated", "deployed",
    "derived", "designed", "determined", "developed", "devised",
    "diagnosed", "directed", "discovered", "dispatched", "displayed",
    "distributed", "documented", "doubled", "drafted",
    "edited", "educated", "effected", "elected", "eliminated",
    "emphasized", "enabled", "encouraged", "enforced", "engaged",
    "engineered", "enhanced", "established", "estimated", "evaluated",
    "examined", "exceeded", "executed", "expanded", "expedited",
    "explained", "extracted", "extrapolated",
    "fabricated", "facilitated", "fashioned", "filed", "financed",
    "fixed", "focused", "forecasted", "formulated", "fortified",
    "fostered", "founded", "furnished",
    "gained", "galvanized", "gathered", "generated", "governed",
    "graduated", "grew", "grouped", "guided",
    "halved", "handled", "hardened", "headed", "helped",
    "hired", "hosted", "hypothesized",
    "identified", "illustrated", "imagined", "implemented", "imported",
    "improved", "improvised", "inaugurated", "incorporated", "increased",
    "indicated", "individualized", "influenced", "informed", "initiated",
    "innovated", "instituted", "instructed", "integrated", "interpreted",
    "interviewed", "introduced", "invented", "investigated", "invited",
    "joined", "judged", "justified",
    "launched", "led", "lessened", "leveraged", "licensed",
    "linked", "litigated", "loaded", "localized", "logged",
    "maintained", "managed", "mapped", "marketed", "mastered",
    "maximized", "measured", "mediated", "mentored", "merged",
    "migrated", "minimized", "modeled", "moderated", "modernized",
    "modified", "monitored", "motivated", "mounted", "moved",
    "navigated", "negotiated", "nominated", "normalized",
    "observed", "obtained", "offered", "opened", "operated",
    "optimized", "orchestrated", "ordered", "organized", "oriented",
    "originated", "outlined", "overcame", "overhauled", "oversaw",
    "participated", "partnered", "perceived", "perfected", "performed",
    "persuaded", "pioneered", "planned", "prepared", "presented",
    "preserved", "prevented", "printed", "prioritized", "probed",
    "processed", "produced", "programmed", "projected", "promoted",
    "proposed", "protected", "proved", "provided", "published",
    "purchased", "pursued", "pioneered",
    "qualified", "quantified", "questioned",
    "raised", "ran", "ranked", "rated", "reached",
    "realigned", "realized", "reasoned", "received", "recognized",
    "recommended", "reconciled", "recorded", "recruited", "rectified",
    "redesigned", "reduced", "reengineered", "referred", "refined",
    "reformed", "regained", "regulated", "rehabilitated", "reinforced",
    "reinvigorated", "rejected", "rejuvenated", "remedied", "remodeled",
    "renegotiated", "reorganized", "repaired", "replaced", "replied",
    "reported", "represented", "reproduced", "requested", "rescued",
    "researched", "resolved", "responded", "restored", "restructured",
    "retrieved", "revamped", "revealed", "reversed", "reviewed",
    "revised", "revitalized", "revolutionized", "rewarded",
    "saved", "scheduled", "screened", "scrutinized", "secured",
    "selected", "separated", "served", "serviced", "settled",
    "shaped", "shared", "shortened", "showcased", "simplified",
    "simulated", "sketched", "sold", "solved", "sorted",
    "sourced", "spearheaded", "specified", "spoke", "sponsored",
    "stabilized", "staffed", "standardized", "started", "stimulated",
    "strategized", "streamlined", "strengthened", "structured", "studied",
    "submitted", "substantiated", "succeeded", "summarized", "supervised",
    "supplied", "supported", "surpassed", "surveyed", "sustained",
    "synthesized", "systematized",
    "tabulated", "targeted", "taught", "terminated", "tested",
    "told", "took", "trained", "transcribed", "transferred",
    "transformed", "translated", "transmitted", "traveled", "treated",
    "troubleshot", "tutored",
    "uncovered", "undertook", "unified", "updated", "upgraded",
    "upheld", "used", "utilized",
    "validated", "valued", "verified", "visualized", "vitally",
    "volunteered",
    "weighed", "welcomed", "widened", "won", "worked",
    "wrote",
}

_ACTION_VERB_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(v) for v in sorted(_ACTION_VERBS, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)


def detect_action_verbs(text: str) -> List[str]:
    if not text or not isinstance(text, str):
        return []
    matches = _ACTION_VERB_PATTERN.findall(text)
    seen = set()
    result = []
    for verb in matches:
        lower = verb.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(verb)
    return result


def analyze_text_action_verbs(text: str) -> Dict[str, Any]:
    verbs = detect_action_verbs(text)
    return {
        "verb_count": len(verbs),
        "verbs_found": verbs,
    }


def analyze_experience_action_verbs(experience: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not experience:
        return {"total_entries": 0, "entries_with_verbs": 0, "entries_without_verbs": 0, "all_verbs": [], "entry_details": []}

    entry_details = []
    all_verbs = []
    entries_with_verbs = 0

    for entry in experience:
        if not isinstance(entry, dict):
            continue
        desc = entry.get("description") or ""
        verbs = detect_action_verbs(desc)
        verb_count = len(verbs)
        if verb_count > 0:
            entries_with_verbs += 1
        all_verbs.extend(verbs)
        entry_details.append({
            "has_action_verb": verb_count > 0,
            "verb_count": verb_count,
            "verbs": verbs,
        })

    total = len(entry_details)
    return {
        "total_entries": total,
        "entries_with_verbs": entries_with_verbs,
        "entries_without_verbs": total - entries_with_verbs,
        "all_verbs": list(dict.fromkeys(all_verbs)),
        "entry_details": entry_details,
    }

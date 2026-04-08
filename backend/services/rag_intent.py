"""Detect greetings / meta questions so we skip irrelevant retrieval and citations."""

from __future__ import annotations

import re


def looks_bengali(text: str) -> bool:
    return any("\u0980" <= c <= "\u09ff" for c in text)


def is_greeting_or_meta(question: str) -> bool:
    """True for hellos, thanks, who-are-you, short Bengali pleasantries — not factual labour queries."""
    s = question.strip()
    if not s or len(s) > 160:
        return False
    low = s.lower()

    if re.fullmatch(
        r"(hi+|hello|hey|yo|howdy|hiya)([\s,!.…]+(there|friend|buddy|mate))?\s*[!?.…]*",
        low,
    ):
        return True
    if re.fullmatch(
        r"(good\s+(morning|afternoon|evening|day)|g'?day)\s*[!?.…]*",
        low,
    ):
        return True
    if re.fullmatch(r"(thanks?|thank\s+you|thx|ty)\s*[!?.…]*", low):
        return True
    if re.fullmatch(
        r"(what\'?s\s+up|whats\s+up|sup|wassup)\s*[!?.…]*",
        low,
    ):
        return True
    if re.fullmatch(
        r"(who\s+are\s+you|what\s+are\s+you|what\s+can\s+you(\s+do)?)\s*[!?.…]*",
        low,
    ):
        return True

    if not any(ch.isdigit() for ch in s) and looks_bengali(s) and len(s) < 55:
        if re.search(
            r"হ্যালো|হাই|হেই|আস-সালাম|আস\s*সালাম|সালাম|সুপ্রভাত|শুভ\s+সকাল|"
            r"কেমন\s+আছ|কেমন\s+আছেন|ধন্যবাদ|নমস্কার",
            s,
        ):
            return True

    return False


def greeting_reply(question: str, forced_language: str | None = None) -> str:
    """Warm, human intro — no legal claims (no retrieval)."""
    use_bn = forced_language == "bn" or (forced_language is None and looks_bengali(question))
    if use_bn:
        return (
            "হ্যালো! আমি GarmentAI। "
            "আমি এখানে আপনার পাশে দাঁড়াতে চাই—কারখানার নিয়ম, ছুটি, মজুরি, নিরাপত্তা "
            "এসব নিয়ে যেন মাথা ঘামাতে না হয়, সেভাবেই সহজ বাংলায় বলব। "
            "যখন প্রশ্ন করবেন, তখন আমি আপনার কারখানার জমা দেওয়া নথি থেকে মিলিয়ে উত্তর দেব। "
            "চাইলে জিজ্ঞেস করতে পারেন: সাপ্তাহিক ছুটি, মাতৃত্বকালীন ছুটি, ওভারটাইম, বা আগুন লাগলে কী করবেন—"
            "বাংলা বা ইংরেজি, যেটা আপনার সুবিধা।"
        )
    return (
        "Hey — nice to meet you. I'm GarmentAI. "
        "I'm here to help you understand your workplace in plain language: leave, wages, safety, "
        "and the rules that matter on the floor — based on your factory's own uploaded documents, "
        "not random internet advice. "
        "Whenever you're ready, ask in English or Bengali (for example: weekly holiday, maternity leave, "
        "overtime pay, or what to do in a fire)."
    )

"""From-scratch oral form generation helpers (MOCK synthesis)."""
from __future__ import annotations

import re
from typing import Any
from ulid import ULID


def _new_step_id() -> str:
    return f"s_{str(ULID()).lower()[:10]}"


def _default_options(step_type: str) -> list[dict[str, str]]:
    if step_type in ("single", "multi"):
        return [
            {"value": "opt_a", "label": "選項 A"},
            {"value": "opt_b", "label": "選項 B"},
        ]
    return []


def _rating_options() -> list[dict[str, str]]:
    return [
        {"value": "5", "label": "非常滿意"},
        {"value": "4", "label": "滿意"},
        {"value": "3", "label": "普通"},
        {"value": "2", "label": "不滿意"},
        {"value": "1", "label": "非常不滿意"},
    ]


def _make_step(
    title: str,
    step_type: str,
    *,
    required: bool = False,
    options: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "id": _new_step_id(),
        "type": step_type,
        "title": title,
        "required": required,
        "options": options if options is not None else _default_options(step_type),
        "showIf": None,
    }


def _is_from_scratch_intent(user_text: str, steps_empty: bool) -> bool:
    """Detect oral create / full-form generation intents."""
    patterns = (
        r"做一份",
        r"幫我做",
        r"產生",
        r"生成",
        r"建立問卷",
        r"建立一份",
        r"從零",
        r"從頭",
        r"全新",
        r"設計一份",
        r"設計一張",
        r"做個問卷",
        r"做個表單",
        r"create.*(form|survey|questionnaire)",
        r"generate.*(form|survey)",
    )
    if any(re.search(p, user_text, re.I) for p in patterns):
        return True
    if steps_empty and any(
        k in user_text
        for k in (
            "問卷",
            "表單",
            "調查",
            "滿意度",
            "報名",
            "諮詢",
            "回饋",
            "評分",
            "預約",
            "申請",
        )
    ):
        return True
    return False


def _infer_form_kind(user_text: str) -> str:
    if any(k in user_text for k in ("滿意度", "滿意", "評分", "服務品質", "顧客", "客戶")):
        return "satisfaction"
    if any(k in user_text for k in ("報名", "活動", "參加", "報到")):
        return "signup"
    if any(k in user_text for k in ("諮詢", "預約", "問診", "聯絡")):
        return "inquiry"
    if any(k in user_text for k in ("回饋", "意見", "建議", "feedback")):
        return "feedback"
    if any(k in user_text for k in ("申請", "表單", "登記")):
        return "application"
    return "generic"


def _infer_schema_title(user_text: str, kind: str) -> str:
    m = re.search(r"[「『\"]([^」』\"]+)[」』\"]", user_text)
    if m:
        t = m.group(1).strip()
        if "問卷" not in t and "表單" not in t and "調查" not in t:
            t = f"{t}問卷"
        return t[:40]
    m = re.search(
        r"(?:幫我)?(?:做|產生|生成|建立|設計)?(?:一份|一張|一個)?"
        r"([^\s，。、]{2,24}?(?:問卷|調查|表單|報名表))",
        user_text,
    )
    if m:
        t = m.group(1).strip(" 「」『』\"'")
        t = re.sub(r"^(?:幫我|請|麻煩)", "", t)
        if t:
            return t[:40]
    defaults = {
        "satisfaction": "顧客滿意度問卷",
        "signup": "活動報名表",
        "inquiry": "諮詢預約表",
        "feedback": "意見回饋問卷",
        "application": "申請登記表",
        "generic": "新問卷",
    }
    return defaults.get(kind, "新問卷")

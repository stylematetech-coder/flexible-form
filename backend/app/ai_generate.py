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
        for k in ("問卷", "表單", "調查", "滿意度", "報名", "諮詢", "回饋", "評分", "預約", "申請")
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


def _synthesize_full_form(user_text: str) -> tuple[list[dict[str, Any]], str]:
    """Build 4–8 reasonable steps from keywords. Returns (steps, schema_title)."""
    kind = _infer_form_kind(user_text)
    title = _infer_schema_title(user_text, kind)
    want_rating = any(k in user_text for k in ("評分", "分數", "星", "滿意"))
    want_suggest = any(k in user_text for k in ("建議", "意見", "回饋", "備註", "其他"))
    steps: list[dict[str, Any]] = []
    if kind == "satisfaction":
        steps.append(_make_step("感謝您抽空填寫！請依實際體驗作答。", "info"))
        steps.append(_make_step("整體滿意度", "single", required=True, options=_rating_options()))
        steps.append(_make_step("服務態度評分（1–5）", "number", required=True))
        steps.append(_make_step("您最滿意的面向（可複選）", "multi", required=False, options=[
            {"value": "speed", "label": "處理速度"}, {"value": "quality", "label": "品質"},
            {"value": "attitude", "label": "服務態度"}, {"value": "price", "label": "價格"},
        ]))
        steps.append(_make_step("是否願意再次使用／推薦？", "single", required=True, options=[
            {"value": "yes", "label": "願意"}, {"value": "maybe", "label": "再考慮"}, {"value": "no", "label": "不願意"},
        ]))
        steps.append(_make_step("其他建議或想告訴我們的話", "textarea", required=False))
    elif kind == "signup":
        steps.append(_make_step("歡迎報名！請填寫以下資料。", "info"))
        steps.append(_make_step("參加者姓名", "text", required=True))
        steps.append(_make_step("聯絡電話", "text", required=True))
        steps.append(_make_step("電子信箱", "text", required=False))
        steps.append(_make_step("參加場次", "single", required=True, options=[
            {"value": "am", "label": "上午場"}, {"value": "pm", "label": "下午場"}, {"value": "full", "label": "全日"},
        ]))
        steps.append(_make_step("飲食／特殊需求（可複選）", "multi", required=False, options=[
            {"value": "veg", "label": "素食"}, {"value": "no_nuts", "label": "過敏（堅果）"}, {"value": "other", "label": "其他"},
        ]))
        steps.append(_make_step("備註", "textarea", required=False))
    elif kind == "inquiry":
        steps.append(_make_step("請留下諮詢需求，我們會盡快回覆。", "info"))
        steps.append(_make_step("您的稱呼", "text", required=True))
        steps.append(_make_step("聯絡方式（電話或 Email）", "text", required=True))
        steps.append(_make_step("諮詢類型", "single", required=True, options=[
            {"value": "product", "label": "產品相關"}, {"value": "service", "label": "服務／流程"},
            {"value": "price", "label": "報價"}, {"value": "other", "label": "其他"},
        ]))
        steps.append(_make_step("希望回覆時段", "text", required=False))
        steps.append(_make_step("諮詢內容說明", "textarea", required=True))
    elif kind == "feedback":
        steps.append(_make_step("歡迎提供意見，協助我們改進。", "info"))
        steps.append(_make_step("意見類型", "single", required=True, options=[
            {"value": "praise", "label": "稱讚"}, {"value": "suggest", "label": "建議"}, {"value": "complaint", "label": "投訴"},
        ]))
        steps.append(_make_step("整體評分（1–10）", "number", required=False))
        steps.append(_make_step("詳細說明", "textarea", required=True))
        steps.append(_make_step("是否希望我們聯繫您？", "single", required=False, options=[
            {"value": "yes", "label": "是"}, {"value": "no", "label": "否"},
        ]))
    elif kind == "application":
        steps.append(_make_step("請完整填寫申請資料。", "info"))
        steps.append(_make_step("申請人姓名", "text", required=True))
        steps.append(_make_step("身分證字號／統一編號", "text", required=False))
        steps.append(_make_step("聯絡電話", "text", required=True))
        steps.append(_make_step("申請項目", "single", required=True, options=[
            {"value": "a", "label": "項目 A"}, {"value": "b", "label": "項目 B"}, {"value": "c", "label": "項目 C"},
        ]))
        steps.append(_make_step("申請說明", "textarea", required=True))
    else:
        steps.append(_make_step("歡迎填寫本問卷。", "info"))
        steps.append(_make_step("您的身份／角色", "single", required=True, options=[
            {"value": "individual", "label": "個人"}, {"value": "business", "label": "企業"}, {"value": "other", "label": "其他"},
        ]))
        if want_rating:
            steps.append(_make_step("整體評分", "single", required=True, options=_rating_options()))
            steps.append(_make_step("分數（1–10）", "number", required=False))
        else:
            steps.append(_make_step("主要需求或主題", "text", required=True))
            steps.append(_make_step("感興趣的項目（可複選）", "multi", required=False, options=[
                {"value": "a", "label": "選項 A"}, {"value": "b", "label": "選項 B"}, {"value": "c", "label": "選項 C"},
            ]))
        steps.append(_make_step("其他建議或補充說明", "textarea", required=False))
    if len(steps) < 4:
        steps.append(_make_step("補充說明", "textarea", required=False))
    if len(steps) > 8:
        steps = steps[:8]
    return steps, title

"""Pluggable AI for form definition edits (Ollama Cloud, OpenAI-compatible, or deterministic MOCK)."""
from __future__ import annotations

import copy
import json
import os
import re
from typing import Any
from ulid import ULID


def _new_step_id() -> str:
    return f"s_{str(ULID()).lower()[:10]}"


def _clone_def(definition: dict[str, Any]) -> dict[str, Any]:
    return copy.deepcopy(definition)


def _infer_step_type(title: str) -> str:
    t = title.lower()
    if any(k in title for k in ("複選", "多選", "可複選")) or "multi" in t:
        return "multi"
    if any(k in title for k in ("單選", "選擇", "身份", "類型")):
        return "single"
    if any(k in title for k in ("分數", "評分", "數量", "幾", "年齡")) or "number" in t:
        return "number"
    if any(k in title for k in ("建議", "說明", "描述", "意見", "備註")):
        return "textarea"
    if any(k in title for k in ("提示", "說明文字", "資訊")):
        return "info"
    return "text"


def _default_options(step_type: str) -> list[dict[str, str]]:
    if step_type in ("single", "multi"):
        return [
            {"value": "opt_a", "label": "選項 A"},
            {"value": "opt_b", "label": "選項 B"},
        ]
    return []


def mock_chat(
    definition: dict[str, Any],
    messages: list[dict[str, str]],
    schema_title: str | None = None,
) -> tuple[str, dict[str, Any] | None, str | None]:
    """Parse simple zh-TW intents. Returns (reply, proposed_definition, new_schema_title)."""
    if not messages:
        return "請告訴我要怎麼調整問卷，例如「加一題滿意度」或「刪掉就讀學校」。", None, None

    user_text = ""
    for m in reversed(messages):
        if m.get("role") == "user" and (m.get("content") or "").strip():
            user_text = (m.get("content") or "").strip()
            break
    if not user_text:
        return "請輸入中文指令，例如「加一題…」「刪掉…」「改標題…」。", None, None

    proposed = _clone_def(definition)
    steps: list[dict[str, Any]] = list(proposed.get("steps") or [])
    new_title: str | None = None
    replies: list[str] = []

    # Rename schema title: 「改標題…」 / 「標題改成…」 / 「把標題改為…」
    title_patterns = [
        r"(?:改標題|標題改成|把標題改為|標題設為|更改標題)[為成：:\s]*(.+)$",
        r"把[「『\"]?(.+?)[」』\"]?[標題]?改成[「『\"]?(.+?)[」』\"]?",
    ]
    for pat in title_patterns:
        m = re.search(pat, user_text)
        if m:
            if m.lastindex and m.lastindex >= 2:
                new_title = m.group(2).strip(" 「」『』\"'")
            else:
                new_title = m.group(1).strip(" 「」『』\"'")
            if new_title:
                replies.append(f"已將問卷標題改為「{new_title}」。")
            break

    # Also match simpler: 改標題XXX without separator if previous didn't match
    if new_title is None:
        m = re.match(r"^改標題\s*(.+)$", user_text)
        if m:
            new_title = m.group(1).strip(" 「」『』\"'")
            if new_title:
                replies.append(f"已將問卷標題改為「{new_title}」。")

    # Delete step: 「刪掉…」 / 「刪除…」 / 「移除…」
    del_m = re.search(
        r"(?:刪掉|刪除|移除)[題目卡片問題項]*[「『\"]?(.+?)[」』\"]?\s*$",
        user_text,
    )
    if del_m:
        key = del_m.group(1).strip(" 「」『』\"'。.")
        if key:
            before = len(steps)
            steps = [
                s
                for s in steps
                if key not in str(s.get("id", "")) and key not in str(s.get("title", ""))
            ]
            removed = before - len(steps)
            if removed:
                replies.append(f"已刪除 {removed} 題（比對「{key}」）。")
            else:
                replies.append(f"找不到標題或 id 含「{key}」的題目，未做變更。")

    # Add step: 「加一題…」 / 「新增一題…」 / 「加入一題…」
    add_m = re.search(
        r"(?:加一題|新增一題|加入一題|加題|新增題目|加一個題目)[：:\s]*(.+)$",
        user_text,
    )
    if add_m:
        title = add_m.group(1).strip(" 「」『』\"'。.")
        if title:
            step_type = _infer_step_type(title)
            step = {
                "id": _new_step_id(),
                "type": step_type,
                "title": title,
                "required": False,
                "options": _default_options(step_type),
                "showIf": None,
            }
            steps.append(step)
            replies.append(f"已新增一題「{title}」（類型：{step_type}）。")

    proposed["steps"] = steps

    if not replies:
        return (
            "我是 MOCK AI（未設定 OLLAMA_API_KEY / OPENAI_API_KEY）。可試：「加一題滿意度評分」、「刪掉就讀學校」、「改標題春季問卷」。",
            None,
            None,
        )

    reply = " ".join(replies) + " 請按「套用到草稿」套用變更。"
    return reply, proposed, new_title


def _assistant_system_prompt() -> str:
    return (
        "你是問卷設計助理。根據目前的 form definition 與使用者對話，"
        "回傳 JSON（不要 markdown）："
        '{"reply":"短繁中回覆","proposed_definition":{完整 FormDefinition 物件或 null},"schema_title":"可選新標題或 null"}。'
        "FormDefinition 結構：version, locale, settings{require_identity, one_response_per}, "
        "steps[{id,type,title,required,options[{value,label}],showIf|{field,op,value}|null}]。"
        "type 僅限 single|multi|text|textarea|number|info。"
        "若無變更，proposed_definition 為 null。"
    )


def _build_context_user_message(
    definition: dict[str, Any],
    messages: list[dict[str, str]],
    schema_title: str | None,
) -> dict[str, str]:
    return {
        "role": "user",
        "content": json.dumps(
            {
                "schema_title": schema_title,
                "current_definition": definition,
                "messages": messages,
            },
            ensure_ascii=False,
        ),
    }


def _strip_markdown_fences(text: str) -> str:
    s = (text or "").strip()
    if not s.startswith("```"):
        return s
    s = re.sub(r"^```(?:json|JSON)?\s*\n?", "", s)
    s = re.sub(r"\n?```\s*$", "", s)
    return s.strip()


def _parse_ai_json_content(content: str) -> tuple[str, dict[str, Any] | None, str | None]:
    """Parse model JSON content into (reply, proposed_definition, schema_title).

    On parse failure return a clear zh-TW error reply and proposed_definition=null.
    """
    raw = _strip_markdown_fences(content)
    try:
        parsed = json.loads(raw)
    except Exception:
        m = re.search(r"\{[\s\S]*\}", raw)
        if not m:
            return (
                "模型回傳無法解析為 JSON，請再試一次或改用更簡短的指令。",
                None,
                None,
            )
        try:
            parsed = json.loads(m.group(0))
        except Exception:
            return (
                "模型回傳無法解析為 JSON，請再試一次或改用更簡短的指令。",
                None,
                None,
            )

    if not isinstance(parsed, dict):
        return ("模型回傳格式不正確（非物件），請再試一次。", None, None)

    reply = str(parsed.get("reply") or "已處理。")
    proposed = parsed.get("proposed_definition")
    title = parsed.get("schema_title")
    if proposed is not None and not isinstance(proposed, dict):
        proposed = None
    if title is not None:
        title = str(title) or None
    return reply, proposed, title


def ollama_cloud_chat(
    definition: dict[str, Any],
    messages: list[dict[str, str]],
    schema_title: str | None = None,
) -> tuple[str, dict[str, Any] | None, str | None]:
    """Call Ollama Cloud chat; expect JSON with reply + proposed_definition (+ optional schema_title)."""
    import urllib.request

    api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    base = os.getenv("OLLAMA_BASE_URL", "https://ollama.com").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")

    payload_msgs = [
        {"role": "system", "content": _assistant_system_prompt()},
        _build_context_user_message(definition, messages, schema_title),
    ]

    body = json.dumps(
        {
            "model": model,
            "messages": payload_msgs,
            "stream": False,
            "format": "json",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{base}/api/chat",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    message = data.get("message") or {}
    content = message.get("content") if isinstance(message, dict) else None
    if content is None:
        return (
            "Ollama 回傳缺少 message.content，請稍後再試。",
            None,
            None,
        )
    return _parse_ai_json_content(str(content))


def openai_chat(
    definition: dict[str, Any],
    messages: list[dict[str, str]],
    schema_title: str | None = None,
) -> tuple[str, dict[str, Any] | None, str | None]:
    """Call OpenAI-compatible chat; expect JSON with reply + proposed_definition (+ optional schema_title)."""
    import urllib.request

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    payload_msgs = [
        {"role": "system", "content": _assistant_system_prompt()},
        _build_context_user_message(definition, messages, schema_title),
    ]

    body = json.dumps(
        {
            "model": model,
            "messages": payload_msgs,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    content = data["choices"][0]["message"]["content"]
    return _parse_ai_json_content(str(content))


def run_ai_chat(
    definition: dict[str, Any],
    messages: list[dict[str, str]],
    schema_title: str | None = None,
) -> tuple[str, dict[str, Any] | None, str | None]:
    if os.getenv("OLLAMA_API_KEY", "").strip():
        try:
            return ollama_cloud_chat(definition, messages, schema_title)
        except Exception as e:
            reply, proposed, title = mock_chat(definition, messages, schema_title)
            return f"（Ollama 呼叫失敗，改用 MOCK：{e}）{reply}", proposed, title
    if os.getenv("OPENAI_API_KEY", "").strip():
        try:
            return openai_chat(definition, messages, schema_title)
        except Exception as e:
            # Fall back to mock with error note
            reply, proposed, title = mock_chat(definition, messages, schema_title)
            return f"（OpenAI 呼叫失敗，改用 MOCK：{e}）{reply}", proposed, title
    return mock_chat(definition, messages, schema_title)

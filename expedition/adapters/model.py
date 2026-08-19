"""Swappable reviewer: Vertex Flash-Lite first, then 3.7 Flash, then Azure Luna."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
import hashlib
from pathlib import Path

PROJECT = "gen-lang-client-0261050164"
CACHE_DIR = Path(__file__).resolve().parents[1] / "var" / "cache" / "model"

DEFAULT_MODELS = [
    ("vertex", "gemini-3.5-flash-lite", {"thinkingConfig": {"thinkingLevel": "MINIMAL"}}),
    ("vertex", "gemini-3.7-flash", {"thinkingConfig": {"thinkingLevel": "LOW"}}),
    ("azure", os.environ.get("AZURE_OPENAI_DEPLOYMENT") or "gpt-5.6-luna", {}),
]


def _env() -> dict[str, str]:
    out = dict(os.environ)
    for path in (
        Path.home() / ".config/agent-keys.env",
        Path.home() / ".config/t3code-agent.env",
    ):
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if line.startswith("export "):
                line = line[7:]
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                out.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return out


def _adc() -> str:
    return subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
    ).strip()


def _vertex(model: str, prompt: str, gen: dict) -> tuple[str, dict]:
    url = (
        f"https://aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/global"
        f"/publishers/google/models/{model}:generateContent"
    )
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 512, "temperature": 0, **gen},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={
            "Authorization": f"Bearer {_adc()}",
            "Content-Type": "application/json",
            "X-Goog-User-Project": PROJECT,
        },
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read().decode())
    text = ""
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        text += part.get("text") or ""
    return text, {"provider": "vertex", "model": model, "usage": data.get("usageMetadata")}


def _azure(deployment: str, prompt: str) -> tuple[str, dict]:
    env = _env()
    base = (env.get("AZURE_OPENAI_BASE_URL") or "").rstrip("/")
    key = env.get("AZURE_OPENAI_API_KEY")
    if not base or not key:
        raise RuntimeError("azure_not_configured")
    url = f"{base}/openai/deployments/{deployment}/chat/completions?api-version=2024-10-21"
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 512,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        method="POST",
        headers={"api-key": key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=40) as resp:
        data = json.loads(resp.read().decode())
    text = data["choices"][0]["message"]["content"]
    return text, {"provider": "azure", "model": deployment, "usage": data.get("usage")}


def complete(prompt: str, prefer: str | None = None) -> dict:
    errors = []
    order = list(DEFAULT_MODELS)
    if prefer == "luna":
        order = [m for m in order if m[0] == "azure"] + [m for m in order if m[0] != "azure"]
    for provider, name, gen in order:
        try:
            if provider == "vertex":
                text, meta = _vertex(name, prompt, gen)
            else:
                text, meta = _azure(name, prompt)
            return {"text": text, "ok": True, **meta}
        except Exception as exc:
            errors.append(f"{provider}:{name}:{type(exc).__name__}")
    return {"text": "", "ok": False, "errors": errors, "provider": None, "model": None}


SKEPTIC_PROMPT = """You are a constrained evidence reviewer. You do not decide the verdict.
Read the JSON evidence graph. Return JSON only:
{"flags":["shared_source"|"geometry_mismatch"|"stale"|"failed_as_pass"|"capacity_from_proximity"|"clean"],
 "notes":"one sentence"}
Flag only defects that are visible in the graph. Do not invent facts.
"""


def _deterministic_prechecks(graph: dict) -> list[str]:
    flags: list[str] = []
    candidates = set(graph.get("candidates") or [])
    atoms = graph.get("atoms") or []
    verdicts = graph.get("verdicts") or []
    gaps = graph.get("gaps") or []
    if any(a.get("status") == "stale" for a in atoms):
        flags.append("stale")
    if any(
        a.get("candidate_id") not in candidates
        for a in atoms
        if a.get("candidate_id") is not None and candidates
    ):
        flags.append("geometry_mismatch")
    if any(v.get("verdict") == "strong_fit" for v in verdicts) and any(
        a.get("decision_effect") in {"VETO", "GATE"}
        and (a.get("kind") in {"FAILED", "UNKNOWN"} or a.get("status") in {"failed", "blocked"})
        for a in atoms
    ):
        flags.append("failed_as_pass")
    gap_names = {
        gap.get("question_id") or gap.get("missing_authority")
        for gap in gaps
        if isinstance(gap, dict)
    }
    has_capacity_proxy = any(
        a.get("field_id") in {
            "nearest_substation_distance_m",
            "nearest_substation_max_voltage_kv",
            "substations_within_radius_count",
        }
        for a in atoms
    )
    if has_capacity_proxy and "electrical_capacity" not in gap_names:
        flags.append("capacity_from_proximity")
    return flags


def skeptic_review(graph: dict, *, live_model: bool = True) -> dict:
    deterministic_flags = _deterministic_prechecks(graph)
    safe = {
        "candidates": graph.get("candidates"),
        "atoms": [
            {
                "field_id": a.get("field_id"),
                "kind": a.get("kind"),
                "status": a.get("status"),
                "independence_group": a.get("independence_group"),
                "decision_effect": a.get("decision_effect"),
                "authority": a.get("authority"),
                "support_kind": (a.get("support") or {}).get("kind"),
                "value_present": a.get("value") is not None,
            }
            for a in graph.get("atoms", [])
        ],
        "verdicts": graph.get("verdicts"),
        "gaps": graph.get("gaps"),
    }
    cache_key = hashlib.sha256(
        json.dumps(safe, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    cache_path = CACHE_DIR / f"skeptic-{cache_key}.json"
    cached = False
    if cache_path.exists():
        try:
            result = json.loads(cache_path.read_text())
            cached = True
        except (json.JSONDecodeError, OSError):
            result = {"text": "", "ok": False, "provider": None, "model": None}
    elif live_model:
        result = complete(SKEPTIC_PROMPT + "\n" + json.dumps(safe)[:8000])
        if result.get("ok"):
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(result, indent=2))
    else:
        result = {"text": "", "ok": False, "provider": None, "model": None}
    flags = []
    notes = ""
    if result.get("ok") and result.get("text"):
        try:
            start = result["text"].find("{")
            end = result["text"].rfind("}") + 1
            parsed = json.loads(result["text"][start:end])
            flags = parsed.get("flags") or []
            notes = parsed.get("notes") or ""
        except Exception:
            notes = "reviewer returned unparseable text"
    else:
        notes = "reviewer unavailable in replay; deterministic prechecks completed"
    merged_flags = list(dict.fromkeys(deterministic_flags + flags))
    if not merged_flags:
        merged_flags = ["clean"]
    return {
        "stamp": "SKEPTIC REVIEW",
        "flags": merged_flags,
        "deterministic_flags": deterministic_flags,
        "model_flags": flags,
        "notes": notes,
        "model": result.get("model"),
        "provider": result.get("provider"),
        "ok": result.get("ok", False),
        "cached": cached,
    }

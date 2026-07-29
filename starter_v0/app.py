from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"

st.set_page_config(page_title="Day04 Research Agent", page_icon="🔎", layout="wide")


def artifact_files(pattern: str) -> list[str]:
    return sorted(p.name for p in ARTIFACTS_DIR.glob(pattern))


def start_session(version, provider_name, model, prompt_path, tools_path) -> None:
    av = build_artifact_version(version, prompt_path, tools_path)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    tid = f"{safe_slug(version)}_{safe_slug(provider_name)}_ui_{stamp}"
    st.session_state.artifact_version = av
    st.session_state.history = []
    st.session_state.turns = []
    st.session_state.transcript_path = TRANSCRIPTS_DIR / f"{tid}.transcript.json"
    st.session_state.transcript = {
        "transcript_id": tid,
        **artifact_version_dict(av),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(prompt_path),
        "tools": str(tools_path),
        "interface": "streamlit",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }


def render_turn(turn: dict) -> None:
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        if turn.get("status") == "provider_error":
            st.error(turn.get("error", "provider error"))
        else:
            st.markdown(turn.get("assistant_text") or "_(trống)_")
        st.caption(
            f"status: `{turn.get('status')}` · "
            f"artifact_version: `{turn.get('artifact_version')}` · "
            f"turn {turn.get('turn_index')}"
        )
        rounds = turn.get("rounds") or []
        if not rounds:
            return
        n_calls = sum(len(r.get("tool_calls") or []) for r in rounds)
        with st.expander(f"🔧 Tool trace — {len(rounds)} round, {n_calls} tool call"):
            for rd in rounds:
                st.markdown(f"**Round {rd['round']}**")
                if not rd.get("tool_calls"):
                    st.caption("_không gọi tool_")
                for ev in rd.get("tool_results") or []:
                    result = ev.get("result")
                    error = result.get("error") if isinstance(result, dict) else None
                    st.markdown(f"`{ev['tool']}` — {'🔴 error' if error else '🟢 ok'}")
                    st.caption("args")
                    st.code(json.dumps(ev.get("args", {}), ensure_ascii=False, indent=2), language="json")
                    st.caption("result")
                    st.code(
                        json.dumps(result, ensure_ascii=False, indent=2, default=str)[:2000],
                        language="json",
                    )
                st.divider()


md_files = artifact_files("*.md")
yaml_files = artifact_files("*.yaml")

with st.sidebar:
    st.header("Cấu hình agent")
    version = st.text_input("Version label", value="v4")
    provider_name = st.selectbox("Provider", ["openai", "openrouter", "anthropic", "gemini"])
    model_override = st.text_input("Model override", value="", placeholder="trống = mặc định")
    prompt_name = st.selectbox(
        "System prompt", md_files,
        index=md_files.index("system_prompt.md") if "system_prompt.md" in md_files else 0,
    )
    tools_name = st.selectbox(
        "Tool declarations", yaml_files,
        index=yaml_files.index("tools.yaml") if "tools.yaml" in yaml_files else 0,
    )
    max_rounds = st.slider("Max tool rounds", 1, 6, 4)
    history_window = st.slider("History window", 0, 10, 5)
    st.divider()
    st.caption("Đổi version/prompt/tools sẽ bắt đầu một phiên mới để so sánh cùng scenario.")

prompt_path = ARTIFACTS_DIR / prompt_name
tools_path = ARTIFACTS_DIR / tools_name
model = model_override.strip() or None

config_sig = (version, provider_name, model, str(prompt_path), str(tools_path))
if st.session_state.get("config_sig") != config_sig:
    start_session(version, provider_name, model, prompt_path, tools_path)
    st.session_state.config_sig = config_sig

av = st.session_state.artifact_version
st.title("🔎 Day04 Research Agent")
c1, c2, c3 = st.columns(3)
c1.metric("artifact_version", av.artifact_version)
c2.metric("prompt_hash", av.prompt_hash[:12])
c3.metric("tools_hash", av.tools_hash[:12])
st.caption(f"Transcript: `{st.session_state.transcript_path.name}`")

declarations = load_tool_declarations(tools_path)
st.caption("Tool khả dụng: " + ", ".join(f"`{d['name']}`" for d in declarations))
st.divider()

for turn in st.session_state.turns:
    render_turn(turn)

user_text = st.chat_input("Nhập yêu cầu cho agent...")
if user_text:
    system_prompt = prompt_path.read_text(encoding="utf-8")
    openai_tools = to_openai_tools(declarations)
    provider = make_provider(provider_name)
    messages = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, history_window),
        {"role": "user", "content": user_text},
    ]
    turn = {
        "turn_index": len(st.session_state.turns) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "artifact_version": av.artifact_version,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }
    with st.spinner("Agent đang chạy..."):
        try:
            result = run_model_tool_loop(
                provider=provider,
                messages=messages,
                tools=openai_tools,
                model=model,
                max_tool_rounds=max_rounds,
            )
            turn.update(result)
            st.session_state.history.append({"role": "user", "content": user_text})
            st.session_state.history.append({"role": "assistant", "content": result["assistant_text"]})
        except Exception as exc:
            turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
    turn["ended_at"] = now_iso()
    st.session_state.turns.append(turn)
    st.session_state.transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
    st.rerun()

"""Small live integration test for Gemini's native tool-calling path.

Uses a synthetic brief and a temporary directory. Never prints credentials,
request headers, or generated client data. Requires GEMINI_API_KEY.
"""
from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

# Direct execution sets sys.path[0] to tests/, so add the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from company.tool_agent import run_tool_agent


def main() -> int:
    if not os.getenv("GEMINI_API_KEY"):
        print("FAIL: GEMINI_API_KEY is missing; native tool-calling cannot be verified.")
        return 1

    relative = Path("agent_workspace/specialists/gemini-live-smoke.md")
    with tempfile.TemporaryDirectory(prefix="gemini-tool-smoke-") as tmp:
        root = Path(tmp)
        brief = {
            "business_name": "Synthetic Gemini Tool Test",
            "service": "landing_page",
            "observed_need": (
                "Integration test only. You MUST use the write_artifact tool to create "
                "agent_workspace/specialists/gemini-live-smoke.md. The file must contain "
                "the exact line: GEMINI_NATIVE_TOOL_CALL_OK. Do not create any other files."
            ),
            "services": ["Synthetic QA"],
            "acceptance_criteria": ["The exact marker is present in the requested file."],
        }
        preferred_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        models = [preferred_model]
        # Provider capacity errors are transient. Try the configured model twice,
        # then a known function-calling-capable fallback without changing production config.
        fallback_model = os.getenv("GEMINI_SMOKE_FALLBACK_MODEL", "gemini-2.5-flash")
        if fallback_model and fallback_model != preferred_model:
            models.append(fallback_model)
        result = None
        last_error = None
        for model_name in models:
            for attempt in range(2):
                try:
                    result = run_tool_agent(brief=brief, workspace=root, max_rounds=8, model=model_name)
                    last_error = None
                    break
                except Exception as exc:
                    last_error = exc
                    message = str(exc)
                    transient = "HTTP 503" in message or "HTTP 429" in message or "high demand" in message.lower()
                    if not transient:
                        safe_detail = str(exc).replace("\\n", " ")[:220]
                        # run_tool_agent sanitizes provider errors; redact the key defensively.
                        safe_detail = safe_detail.replace(os.environ["GEMINI_API_KEY"], "[redacted]")
                        print(f"FAIL: Gemini tool-agent request failed ({type(exc).__name__}): {safe_detail}")
                        return 1
                    if attempt == 0:
                        time.sleep(2)
            if last_error is None:
                break
        if last_error is not None:
            print("FAIL: Gemini native tool calling unavailable after transient retries and fallback model.")
            return 1
        artifact = root / relative
        if int(result.get("tool_calls", 0) or 0) < 1:
            print(f"FAIL: Gemini made no successful tool calls (status={result.get('status', 'unknown')}).")
            return 1
        if not artifact.is_file():
            print(f"FAIL: expected synthetic artifact was not created (status={result.get('status', 'unknown')}, tool_calls={result.get('tool_calls', 0)}).")
            return 1
        if "GEMINI_NATIVE_TOOL_CALL_OK" not in artifact.read_text(encoding="utf-8"):
            print("FAIL: generated artifact did not contain the required marker.")
            return 1

    print("PASS: live Gemini native function call, tool execution, and artifact verification succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

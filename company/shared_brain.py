"""Optional authenticated client for Nexora's shared-brain Edge Function.

Configure SHARED_BRAIN_URL, SUPABASE_PUBLISHABLE_KEY and a short-lived
SUPABASE_ACCESS_TOKEN in the runtime environment. Never commit tokens.
This client fails closed and never logs credentials or memory content.
"""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.request
import time
from typing import Any

DEFAULT_URL = "https://ydstbryiwiigzlqbrcpo.supabase.co/functions/v1/shared-brain"

class SharedBrainError(RuntimeError):
    pass

class SharedBrainClient:
    def __init__(self, *, endpoint: str | None = None, publishable_key: str | None = None,
                 access_token: str | None = None, timeout: float = 8.0):
        self.endpoint = (endpoint or os.getenv("SHARED_BRAIN_URL") or DEFAULT_URL).rstrip("/")
        self.publishable_key = publishable_key or os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
        self.access_token = access_token or os.getenv("SUPABASE_ACCESS_TOKEN", "")
        self.agent_key = os.getenv("SHARED_BRAIN_AGENT_KEY", "")
        self.github_oidc_token = os.getenv("SHARED_BRAIN_GITHUB_OIDC_TOKEN", "")
        self.agent_id = os.getenv("SHARED_BRAIN_AGENT_ID", "company-agent-runtime")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and ((self.publishable_key and self.access_token) or (self.agent_key and self.agent_id) or (self.github_oidc_token and self.agent_id)))

    def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.configured:
            raise SharedBrainError("Shared brain needs agent credentials or a valid user session.")
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.github_oidc_token:
            headers["x-github-oidc-token"] = self.github_oidc_token
            headers["x-agent-id"] = self.agent_id
        elif self.agent_key:
            headers["x-agent-key"] = self.agent_key
            headers["x-agent-id"] = self.agent_id
        else:
            headers["Authorization"] = "Bearer " + self.access_token
            headers["apikey"] = self.publishable_key
        request = urllib.request.Request(self.endpoint, data=data, method="POST", headers=headers)
        # Edge Functions can briefly return 502/503/504 during cold starts or transient
        # upstream faults. Retry only transient failures; never retry auth/validation errors.
        result: Any = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    result = json.loads(response.read(128_000).decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in {502, 503, 504} or attempt == 2:
                    raise SharedBrainError(f"Shared brain returned HTTP {exc.code}.") from None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
                if attempt == 2:
                    raise SharedBrainError("Shared brain is unavailable or returned invalid JSON.") from None
            time.sleep(0.25 * (2 ** attempt))
        if not isinstance(result, dict):
            raise SharedBrainError("Shared brain returned an unexpected response.")
        return result

    def recall(self, *, project_key: str = "nexora", namespace: str = "general",
               query: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "action": "recall", "project_key": project_key,
            "namespace": namespace, "limit": min(50, max(1, int(limit))),
        }
        if query:
            payload["query"] = query[:120]
        result = self._post(payload)
        memories = result.get("memories")
        if not isinstance(memories, list):
            raise SharedBrainError("Shared brain recall response is malformed.")
        return memories

    def remember(self, *, memory_key: str, content: Any, source_agent: str,
                 summary: str = "", project_key: str = "nexora",
                 namespace: str = "general", tags: list[str] | None = None,
                 confidence: float = 0.8, source_ref: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "action": "remember", "project_key": project_key, "namespace": namespace,
            "memory_key": memory_key, "content": content, "source_agent": source_agent,
            "summary": summary, "tags": tags or [], "confidence": confidence,
        }
        if source_ref:
            payload["source_ref"] = source_ref
        return self._post(payload)

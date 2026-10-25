"""Write a minimal workflow-run fact to the shared agent brain.

This records run metadata only (never artifacts, credentials, or raw client briefs).
The caller must configure an approved machine identity (GitHub OIDC for the workflow registry or SHARED_BRAIN_AGENT_KEY for legacy runtimes) and a unique SHARED_BRAIN_AGENT_ID.
"""
from __future__ import annotations
import argparse, json, os, re, sys
from .shared_brain import SharedBrainClient, SharedBrainError

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True, choices=["success", "failure", "cancelled", "skipped", "unknown"])
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID", "manual"))
    parser.add_argument("--commit", default=os.getenv("GITHUB_SHA", "unknown"))
    parser.add_argument("--workflow", default=os.getenv("GITHUB_WORKFLOW", "unknown"))
    parser.add_argument("--repository", default=os.getenv("GITHUB_REPOSITORY", "unknown"))
    args = parser.parse_args()
    agent = os.getenv("SHARED_BRAIN_AGENT_ID", "github-actions")
    safe = re.sub(r"[^a-zA-Z0-9._:-]", "-", f"{args.workflow}:{args.run_id}")[:150]
    client = SharedBrainClient()
    try:
        result = client.remember(
            project_key="nexora", namespace="agent-runs", memory_key=safe,
            source_agent=agent,
            summary=f"Workflow {args.workflow} ended with status {args.status}; run {args.run_id}.",
            content={"workflow": args.workflow, "status": args.status, "run_id": args.run_id,
                     "commit": args.commit, "repository": args.repository, "review_required": args.status != "success"},
            tags=["workflow-run", args.status], confidence=1.0,
            source_ref=f"{args.repository}/actions/runs/{args.run_id}",
        )
        readback = client.recall(
            project_key="nexora", namespace="agent-runs",
            query=f"run {args.run_id}", limit=50,
        )
        verified = any(
            isinstance(item, dict)
            and item.get("memory_key") == safe
            and isinstance(item.get("content"), dict)
            and str(item["content"].get("run_id")) == str(args.run_id)
            for item in readback
        )
        if not verified:
            raise SharedBrainError("Shared brain write/read-back verification failed.")
        print(json.dumps({
            "shared_brain": "saved_and_recalled",
            "scope": result.get("scope", "unknown"),
        }))
        return 0
    except SharedBrainError as exc:
        print(json.dumps({"shared_brain": "unavailable", "reason": str(exc)}))
        # Registry callers can opt into strict mode so green status always means the write succeeded.
        return 1 if os.getenv("SHARED_BRAIN_STRICT", "").strip().lower() in {"1", "true", "yes"} else 0

if __name__ == "__main__":
    sys.exit(main())

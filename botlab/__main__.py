from .workflow import build_reel_draft, save_draft

def main() -> None:
    draft = build_reel_draft("What backtesting can and cannot tell you")
    path = save_draft(draft)
    print(f"Draft saved: {path}")
    print(f"State: {draft['state']} | External publishing enabled: {draft['external_publish_enabled']}")
    print("\n--- SCRIPT ---\n")
    print(draft["script"])

if __name__ == "__main__":
    main()

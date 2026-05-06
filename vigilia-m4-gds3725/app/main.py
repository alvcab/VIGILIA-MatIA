from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from app.config import load_config
from services.access_control.dry_run import DryRunGate
from services.decision.policy import decide_from_text
from services.telephony.call_router import CallRouter
from services.telephony.in_memory import InMemorySessionFactory
from services.tts.canned_audio import build_spoken_response


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIGILIA M4 GDS3725 scaffold")
    parser.add_argument(
        "--mode",
        choices=["decision-only", "dry-run", "session-replay"],
        default=None,
    )
    parser.add_argument("--text", default="", help="Input text for the policy layer")
    parser.add_argument("--caller-id", default="test-intercom", help="Simulated caller id")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = load_config()
    mode = args.mode or config.default_mode

    decision = decide_from_text(args.text)

    if mode == "session-replay":
        session = InMemorySessionFactory().create(
            caller_id=args.caller_id,
            transcript=args.text,
        )
        routed = CallRouter().route(session)
        print(json.dumps(routed, ensure_ascii=True, indent=2))
        return 0

    output = {
        "mode": mode,
        "decision": asdict(decision),
        "spoken_response": build_spoken_response(decision),
    }

    if mode == "dry-run":
        output["gate_action"] = DryRunGate().handle(decision)

    print(json.dumps(output, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

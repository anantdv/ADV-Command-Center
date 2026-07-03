"""Manual proof that ERP row payloads cannot cross the LLM boundary."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.llm.privacy_gateway import PrivacyViolationError, assert_safe_for_external_llm


def main() -> None:
    unsafe = {"records": [{"customer": "ABC", "grand_total": 10000}]}
    try:
        assert_safe_for_external_llm(unsafe)
    except PrivacyViolationError:
        print("Privacy gateway blocked unsafe payload.")
        return
    raise SystemExit("ERROR: unsafe payload was not blocked")


if __name__ == "__main__":
    main()

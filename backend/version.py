"""Version information and utilities."""

import os
from datetime import datetime, timezone

GIT_SHA = os.getenv("GIT_SHA", "dev")
BUILT_AT = os.getenv("BUILT_AT") or datetime.now(timezone.utc).isoformat()


def version_payload() -> dict:
    """Return version information as a dictionary.

    :return: Version information as a dictionary.
    """
    return {"git": GIT_SHA, "builtAt": BUILT_AT}

"""Error classification and retry logic with human fallback."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorClass(str, Enum):
    TRANSIENT = "transient"      # Network timeout, temp file lock
    PERMISSION = "permission"    # Auth/access denied
    NOT_FOUND = "not_found"      # Package/service/file missing
    DEPENDENCY = "dependency"    # Missing dependency
    PERMANENT = "permanent"      # Logic error, bad input


@dataclass
class HealResult:
    should_retry: bool
    modified_command: str | None = None
    error_class: ErrorClass = ErrorClass.PERMANENT
    human_needed: bool = False
    explanation: str = ""


MAX_RETRIES = 3

# Pattern -> (ErrorClass, retryable)
ERROR_PATTERNS: list[tuple[str, ErrorClass, bool]] = [
    ("Connection timed out", ErrorClass.TRANSIENT, True),
    ("Could not resolve", ErrorClass.TRANSIENT, True),
    ("E: Unable to locate package", ErrorClass.NOT_FOUND, False),
    ("Permission denied", ErrorClass.PERMISSION, False),
    ("No such file or directory", ErrorClass.NOT_FOUND, False),
    ("dpkg was interrupted", ErrorClass.TRANSIENT, True),
    ("is another process using it", ErrorClass.TRANSIENT, True),
    ("dependency problems", ErrorClass.DEPENDENCY, False),
]


def classify_and_heal(
    stderr: str,
    exit_code: int,
    attempt: int,
) -> HealResult:
    """Classify an error and decide whether to retry."""
    if exit_code == 0:
        return HealResult(should_retry=False, error_class=ErrorClass.TRANSIENT)

    for pattern, error_class, retryable in ERROR_PATTERNS:
        if pattern in stderr:
            if retryable and attempt < MAX_RETRIES:
                return HealResult(
                    should_retry=True,
                    error_class=error_class,
                    explanation=f"Matched '{pattern}', retry {attempt+1}/{MAX_RETRIES}",
                )
            return HealResult(
                should_retry=False,
                error_class=error_class,
                human_needed=True,
                explanation=f"Error: {pattern} (attempts exhausted)" if retryable
                    else f"Non-retryable error: {pattern}",
            )

    # Unknown error -> escalate to human
    return HealResult(
        should_retry=False,
        error_class=ErrorClass.PERMANENT,
        human_needed=True,
        explanation=f"Unknown error (exit {exit_code}): {stderr[:200]}",
    )

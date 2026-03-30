"""Project-wide constants and label mappings.

This module centralizes the label mappings for the numeric-coded columns
found in the dataset (activity and wrist). Keeping these in one place
avoids duplication and makes the mappings easy to reference from code
and tests.
"""

ACTIVITY_LABELS = {
    0: "walking",
    1: "running",
}

WRIST_LABELS = {
    0: "left",
    1: "right",
}

__all__ = ["ACTIVITY_LABELS", "WRIST_LABELS"]

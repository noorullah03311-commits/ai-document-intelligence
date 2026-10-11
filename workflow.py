WORKFLOW_STATES = ("New", "Processing", "Needs Review", "Approved", "Rejected", "Completed")

VALID_TRANSITIONS = {
    "New": {"Processing"},
    "Processing": {"Needs Review", "Completed"},
    "Needs Review": {"Approved", "Rejected", "Processing"},
    "Approved": {"Completed"},
    "Rejected": set(),
    "Completed": set(),
}

LOW_CONFIDENCE_THRESHOLD = 0.70


def can_transition(previous_state, new_state):
    if previous_state == new_state:
        return True
    return new_state in VALID_TRANSITIONS.get(previous_state, set())


def transition_or_raise(previous_state, new_state):
    if not can_transition(previous_state, new_state):
        raise ValueError(f"Invalid workflow transition: {previous_state} → {new_state}")
    return new_state


def apply_rules(document_type, validation_result, confidence=None):
    errors = validation_result.get("errors", [])
    missing = validation_result.get("missing_fields", [])
    if not validation_result.get("valid", False):
        return {
            "decision": "REVIEW",
            "next_state": "Needs Review",
            "reason": "Validation failed: " + ", ".join(errors or missing)
        }
    if confidence is not None and confidence < LOW_CONFIDENCE_THRESHOLD:
        return {
            "decision": "REVIEW",
            "next_state": "Needs Review",
            "reason": f"Classification confidence {confidence:.1%} is below the {LOW_CONFIDENCE_THRESHOLD:.0%} threshold."
        }
    if document_type not in {"Invoice", "Resume", "Other"}:
        return {
            "decision": "REVIEW",
            "next_state": "Needs Review",
            "reason": "Document type is not supported by the workflow rules."
        }
    return {
        "decision": "COMPLETE",
        "next_state": "Completed",
        "reason": "Required fields passed validation and no review rule was triggered."
    }


def review_decision(approved, reason=""):
    if approved:
        return "Approved", (reason or "Reviewer approved the document.")
    if not reason.strip():
        raise ValueError("A rejection reason is required.")
    return "Rejected", reason.strip()

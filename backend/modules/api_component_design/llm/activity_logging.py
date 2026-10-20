"""Short provider diagnostics without prompts, credentials, or response bodies."""
from contextvars import ContextVar

requirement_context = ContextVar("api_requirement", default="-")


def failure_reason(error):
    seen = set()
    while error.__cause__ is not None and id(error) not in seen:
        seen.add(id(error))
        error = error.__cause__
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    if isinstance(status, int) and 100 <= status <= 599:
        label = {
            400: "invalid request", 401: "authentication rejected",
            403: "access denied", 404: "model or endpoint not found",
            413: "request too large", 429: "rate limit or quota",
            500: "provider error", 502: "gateway error",
            503: "provider unavailable", 504: "timeout",
        }.get(status, "HTTP error")
        return f"{status} {label}"
    name = type(error).__name__
    if "Timeout" in name:
        return "timeout"
    if "Connect" in name:
        return "connection error"
    if name == "ValidationError":
        return "invalid structured response"
    return name

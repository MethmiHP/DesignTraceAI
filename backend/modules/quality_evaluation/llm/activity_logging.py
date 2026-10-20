"""Provider activity logs with identifiers, never prompts, responses, or secrets."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import logging
from time import perf_counter

logger = logging.getLogger('modules.quality_evaluation.llm.activity')
_context = ContextVar('quality_llm_context', default=('-', '-'))


def failure_reason(error):
    """Summarize SDK errors without exposing response bodies or credentials."""
    seen = set()
    while id(error) not in seen:
        seen.add(id(error))
        cause = error.__cause__
        if cause is None:
            break
        error = cause
    status = getattr(error, 'status_code', None)
    if status is None:
        status = getattr(error, 'code', None)
    if isinstance(status, int) and 100 <= status <= 599:
        labels = {
            400: 'invalid request',
            401: 'authentication rejected',
            403: 'access denied',
            404: 'model or endpoint not found',
            408: 'timeout',
            413: 'request too large',
            429: 'rate limit or quota',
            500: 'provider error',
            502: 'provider gateway error',
            503: 'provider unavailable',
            504: 'timeout',
        }
        return f'{status} {labels.get(status, "HTTP error")}'
    name = type(error).__name__
    if 'Timeout' in name:
        return 'timeout'
    if 'Connection' in name or 'ConnectError' in name:
        return 'connection error'
    if name == 'ValidationError':
        return 'invalid structured response'
    return name


@contextmanager
def evaluation_log_context(project_id, rule_id):
    token = _context.set((project_id, rule_id))
    try:
        yield
    finally:
        _context.reset(token)


def log_provider_call(method):
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        _, rule = _context.get()
        started = perf_counter()
        logger.info('[%s] %s started', rule, self.name)
        try:
            result = method(self, *args, **kwargs)
        except Exception as exc:
            logger.warning('[%s] %s failed: %s', rule, self.name, failure_reason(exc))
            raise
        logger.info('[%s] %s OK (%.1fs)', rule, self.name, perf_counter() - started)
        return result
    return wrapped


def log_fallback(previous, next_provider):
    _, rule = _context.get()
    logger.info('[%s] %s -> %s', rule, previous, next_provider)

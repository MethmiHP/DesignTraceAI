"""Security design metadata; does not implement runtime authentication."""
import hashlib
import re

from .schemas import SecurityPolicy
from shared.models.common import ValidationIssue


def apply_security(operation, policy):
    operation.security = policy.model_copy(deep=True)
    if policy.authentication == 'none':
        # Baseline templates include authentication errors by default. An
        # explicit public policy must not retain those implied requirements.
        operation.error_responses.pop('401', None)
        operation.error_responses.pop('403', None)
    if policy.authentication not in {'unspecified', 'none'}:
        operation.error_responses.setdefault('401', 'Authentication required or credentials invalid')
        if policy.roles or policy.access_rules:
            operation.error_responses.setdefault('403', 'Authenticated caller is not permitted to access this resource')


def security_scheme(policy: SecurityPolicy):
    if policy.authentication in {'bearer', 'basic'}:
        name = 'bearerAuth' if policy.authentication == 'bearer' else 'basicAuth'
        return name, {'type': 'http', 'scheme': policy.authentication}
    if policy.authentication == 'api_key':
        signature = f'{policy.api_key_location}:{policy.api_key_name}'
        name = 'apiKey_' + hashlib.sha256(signature.encode()).hexdigest()[:12]
        return name, {'type': 'apiKey', 'in': policy.api_key_location, 'name': policy.api_key_name}
    return None


def requires_authentication(request, requirement, policy):
    text = ' '.join([requirement.statement if requirement else '', *[r.statement for r in request.non_functional_requirements]])
    text = re.sub(r'\b(no authentication required|without authentication|authentication is not required)\b', '', text, flags=re.I)
    return bool(re.search(r'\b(authenticat\w*|jwt|oauth\w*|bearer|logged[ -]in)\b', text, re.I) or policy.roles or policy.access_rules)


def security_configuration_gaps(request):
    """Require a user decision before generation; never infer a mechanism."""
    issues = []
    for index, requirement in enumerate(request.functional_requirements):
        policy = requirement.security or request.security
        if policy.authentication == 'unspecified' and requires_authentication(request, requirement, policy):
            issues.append(ValidationIssue(
                code='SECURITY_CONFIGURATION_REQUIRED',
                message=f'{requirement.requirement_id}: Authentication is required. Choose a mechanism, then save and regenerate.',
                field=f'functional_requirements.{index}.security.authentication',
            ))
    return issues


def validate_security(request, operation, issues):
    requirement = next((r for r in request.functional_requirements if r.requirement_id == operation.requirement_id), None)
    expected = (requirement.security if requirement and requirement.security else request.security)
    policy = operation.security
    def issue(code, message, severity='ERROR'):
        issues.append(ValidationIssue(code=code, message=f'{operation.operation_id}: {message}', severity=severity))
    if policy != expected:
        issue('SECURITY_POLICY_MISMATCH', 'Generated security does not match the supplied security policy.')
    # Explicit structured policy is authoritative. Prose cues request a review;
    # they never silently choose an authentication scheme.
    mentions_auth = requires_authentication(request, requirement, policy)
    if policy.authentication == 'unspecified':
        if mentions_auth or policy.roles or policy.access_rules:
            issue('SECURITY_CONFIGURATION_REQUIRED', 'Security requirements exist, but no authentication scheme was selected.')
        else:
            issue('SECURITY_NOT_SPECIFIED', 'Select an authentication scheme or explicitly mark this endpoint public.', 'WARNING')
    if policy.authentication == 'none' and (policy.roles or policy.access_rules):
        issue('PUBLIC_ENDPOINT_ACCESS_RULES', 'A public endpoint cannot require authenticated roles or ownership rules.')
    if policy.authentication == 'none' and mentions_auth:
        issue('SECURITY_REQUIREMENT_CONFLICT', 'Public access conflicts with authentication wording in the requirements; review the policy.')
    if policy.authentication not in {'unspecified', 'none'}:
        if '401' not in operation.error_responses:
            issue('MISSING_AUTHENTICATION_ERROR', 'A protected endpoint must document a 401 response.')
        if (policy.roles or policy.access_rules) and '403' not in operation.error_responses:
            issue('MISSING_AUTHORIZATION_ERROR', 'Access restrictions require a documented 403 response.')

from security_platform import *


def test_threat_is_denied_and_audited():
    a = AuditLog()
    assert SecurityPolicy().evaluate("r", "prompt injection detected", a) is False
    assert a.events[0].severity == "high"


def test_safe_request():
    a = AuditLog()
    assert SecurityPolicy().evaluate("r", "hello", a) is True and not a.events


def test_multiple_rules_audit():
    a = AuditLog()
    SecurityPolicy().evaluate("r", "credential secret", a)
    assert len(a.events) == 2

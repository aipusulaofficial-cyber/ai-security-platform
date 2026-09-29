import pytest

from security_domain import require_audit_context


@pytest.mark.parametrize("actor,request_id", [("", "id"), (" ", "id"), ("actor", " ")])
def test_blank_audit_context_rejected(actor, request_id):
    with pytest.raises(ValueError):
        require_audit_context(actor, request_id)


def test_valid_audit_context():
    require_audit_context("actor", "request")

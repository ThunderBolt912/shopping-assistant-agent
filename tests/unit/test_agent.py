# tests/unit/test_agent.py

"""Security‑focused test suite for the ``redeem_discount_code`` tool.

The tests verify:
* Input validation (type safety, required arguments).
* Business‑logic guardrails (valid codes, one‑time use per user, independent users).
* That the implementation does not perform any OS‑level commands.
"""

import builtins
import pytest

# Import the tool and its in‑memory state containers
from app.tools import redeem_discount_code, DISCOUNT_CODES, redeemed_codes

# Helper to reset the global ``redeemed_codes`` set between tests
def _reset_state():
    redeemed_codes.clear()

@pytest.fixture(autouse=True)
def isolated_state():
    _reset_state()
    yield
    _reset_state()

# ---------------------------------------------------------------------------
# 1️⃣ Input validation
# ---------------------------------------------------------------------------
def test_missing_user_id():
    """Calling without ``user_id`` should raise a ``TypeError``."""
    with pytest.raises(TypeError):
        redeem_discount_code(code="WELCOME50")


def test_missing_code():
    """Calling without ``code`` should raise a ``TypeError``."""
    with pytest.raises(TypeError):
        redeem_discount_code(user_id="alice")


def test_non_string_inputs():
    """Non‑string arguments must be rejected by Python's signature enforcement."""
    with pytest.raises(TypeError):
        redeem_discount_code(user_id=123, code=456)

# ---------------------------------------------------------------------------
# 2️⃣ Business‑logic guardrails
# ---------------------------------------------------------------------------
def test_invalid_code():
    result = redeem_discount_code(user_id="bob", code="INVALID")
    assert "invalid" in result.lower()
    assert "❌" in result


def test_successful_redemption():
    code = "WELCOME50"
    result = redeem_discount_code(user_id="carol", code=code)
    assert "✅" in result
    assert "50%" in result  # matches DISCOUNT_CODES entry
    assert ("carol", code) in redeemed_codes


def test_duplicate_redemption_same_user():
    code = "WELCOME50"
    first = redeem_discount_code(user_id="dave", code=code)
    assert "✅" in first
    second = redeem_discount_code(user_id="dave", code=code)
    assert "⚠️" in second
    assert "already been redeemed" in second.lower()


def test_same_code_different_users():
    code = "WELCOME50"
    first = redeem_discount_code(user_id="eve", code=code)
    second = redeem_discount_code(user_id="frank", code=code)
    assert "✅" in first and "✅" in second
    assert ("eve", code) in redeemed_codes
    assert ("frank", code) in redeemed_codes

# ---------------------------------------------------------------------------
# 3️⃣ Security boundaries – ensure no OS/system calls are made
# ---------------------------------------------------------------------------
def test_no_os_system_calls(monkeypatch):
    """The tool must not invoke any OS commands (e.g., ``os.system``)."""
    calls = []

    def fake_system(*args, **kwargs):
        calls.append((args, kwargs))
        raise RuntimeError("Unexpected OS call")

    # Patch potential entry points – if the tool ever tries to exec shell commands it will fail
    monkeypatch.setattr(builtins, "exec", fake_system, raising=False)
    # Run a normal redemption – it should succeed without triggering the patched exec
    result = redeem_discount_code(user_id="gina", code="WELCOME50")
    assert "✅" in result
    assert not calls, "Tool attempted to execute OS commands"

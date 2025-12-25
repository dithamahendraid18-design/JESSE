from pathlib import Path
from jesse.core.client_loader import load_client
from jesse.services.response_service import get_greeting, get_intent_response


def test_greeting_has_buttons():
    root = Path(__file__).resolve().parents[2]
    ctx = load_client(root / "clients", "oceanbite_001")
    reply, buttons = get_greeting(ctx)
    assert reply
    assert isinstance(buttons, list)


def test_fallback_exists():
    root = Path(__file__).resolve().parents[2]
    ctx = load_client(root / "clients", "oceanbite_001")
    reply, buttons = get_intent_response(ctx, "fallback")
    assert reply
    assert isinstance(buttons, list)

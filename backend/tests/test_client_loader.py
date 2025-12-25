from pathlib import Path
from jesse.core.client_loader import load_client


def test_load_client():
    root = Path(__file__).resolve().parents[2]
    clients_dir = root / "clients"
    ctx = load_client(clients_dir, "oceanbite_001")
    assert ctx.name
    assert isinstance(ctx.responses, dict)

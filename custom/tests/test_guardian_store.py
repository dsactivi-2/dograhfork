import importlib.util
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["STATE_DIR"] = "/tmp/guardian-state-test"
os.environ["REPO_ROOT"] = "/tmp"
os.environ["OVERLAY_ROOT"] = "/tmp/no-overlay"

spec = importlib.util.spec_from_file_location(
    "guardian_store", ROOT / "custom" / "guardian" / "web" / "store.py"
)
store = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(store)
store.STATE = Path(os.environ["STATE_DIR"])


def setup_function():
    store.STATE.mkdir(parents=True, exist_ok=True)
    for path in store.STATE.rglob("*"):
        if path.is_file():
            path.unlink()


def test_save_records_history_and_redacts_keys():
    saved = store.save_config(
        {"fish": {"api_key": "super-secret", "voice": "abc", "model": "s2.1-pro"}},
        actor="test",
        source="unit",
    )
    assert saved["fish"]["voice"] == "abc"
    events = store.list_history(10)
    assert events[0]["action"] == "config.set"
    assert events[0]["after"]["fish"]["api_key"] == "***"
    env = store.runtime_env_path().read_text()
    assert "DEEPGRAM_BASE_URL=" in env


def test_redact_nested():
    out = store.redact({"deepgram_stt": {"api_key": "x", "model": "nova-3-general"}})
    assert out["deepgram_stt"]["api_key"] == "***"
    assert out["deepgram_stt"]["model"] == "nova-3-general"

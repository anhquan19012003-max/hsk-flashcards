"""Where the private working files live and where the password comes from (specs/mock-tests.md sections 0 and 11)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def private_dir() -> Path:
    """BANK_PRIVATE_DIR, else ../hsk-bank-private if it exists, else mock-tests/."""
    env = os.environ.get("BANK_PRIVATE_DIR")
    if env:
        return Path(env).expanduser().resolve()
    sibling = ROOT.parent / "hsk-bank-private"
    if sibling.is_dir():
        return sibling
    return ROOT / "mock-tests"


def get_password(private: Path = None) -> str:
    """BANK_PASSWORD first, then <private>/.bank-password. Never printed, never written anywhere."""
    pw = os.environ.get("BANK_PASSWORD")
    if pw:
        return pw
    f = (private or private_dir()) / ".bank-password"
    if f.is_file():
        text = f.read_text(encoding="utf-8").strip()
        if text:
            return text
    raise SystemExit("No bank password: set BANK_PASSWORD or create mock-tests/.bank-password (ask Quan).")
